#!/usr/bin/env python3
"""Extract the Forza Horizon 1 Xenos shader corpus from retail .fxobj files."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import struct
import tempfile
from pathlib import Path
from zipfile import BadZipFile, ZipFile


CONTAINER = struct.Struct(">9I")
SHADER = struct.Struct(">6I")
VERTEX_SHADER = struct.Struct(">9I")
FLAGS_MASK = 0xFFFFFF00
FLAGS_MAGIC = 0x102A1100
FORMAT_WORDS = {
    6: 1, 7: 1, 16: 1, 17: 1, 25: 1, 26: 2, 31: 1, 32: 2,
    33: 1, 34: 2, 35: 4, 36: 1, 37: 2, 38: 4, 57: 3,
}


def extract_declarations(data: bytes) -> list[tuple[tuple, tuple[int, ...]]]:
    if len(data) < 28 or struct.unpack_from(">I", data)[0] != 0x101:
        return []
    shader_size, technique_count, declaration_count, stride_count = struct.unpack_from(
        ">4I", data, 8
    )
    table_count = technique_count + declaration_count * 2 + stride_count
    if table_count > (len(data) - 28) // 4:
        return []
    table = struct.unpack_from(f">{table_count}I", data, 28)
    declaration_sizes = table[technique_count : technique_count + declaration_count]
    stride_lengths = table[
        technique_count + declaration_count : technique_count + declaration_count * 2
    ]
    strides = table[technique_count + declaration_count * 2 :]
    offset = 28 + table_count * 4 + shader_size
    stride_offset = 0
    result = []
    for declaration_size, stride_length in zip(declaration_sizes, stride_lengths):
        if offset + declaration_size > len(data) or declaration_size < 52:
            return []
        count = struct.unpack_from(">I", data, offset + 24)[0]
        if 52 + count * 12 > declaration_size or stride_offset + stride_length > len(strides):
            return []
        elements = []
        for index in range(count):
            element_offset = offset + 52 + index * 12
            stream, byte_offset, element_type = struct.unpack_from(">HHI", data, element_offset)
            usage, usage_index = struct.unpack_from("BB", data, element_offset + 9)
            elements.append((stream, byte_offset, element_type, usage, usage_index))
        result.append((tuple(elements), tuple(strides[stride_offset : stride_offset + stride_length])))
        stride_offset += stride_length
        offset += declaration_size
    return result


def patch_vertex_shader(code: bytes, shader_elements: tuple, declaration: tuple) -> bytes | None:
    declared_elements, strides = declaration
    declared_by_semantic = {(item[3], item[4]): item for item in declared_elements}
    words = list(struct.unpack(f">{len(code) // 4}I", code))
    streams: dict[int, list[tuple[int, tuple]]] = {}
    resolved = []
    for address, usage, usage_index in shader_elements:
        element = declared_by_semantic.get((usage, usage_index))
        if element is None or element[0] >= len(strides):
            return None
        resolved.append((address, element))
        streams.setdefault(element[0], []).append((address, element))
    for address, (stream, byte_offset, element_type, _, _) in resolved:
        vertex_format = element_type & 0x3F
        if (address * 3 + 2 >= len(words) or strides[stream] % 4 or byte_offset % 4
                or vertex_format not in FORMAT_WORDS):
            return None
        first = address == min(item[0] for item in streams[stream])
        used_words = max(
            item[1] // 4 + FORMAT_WORDS[item[2] & 0x3F]
            for _, item in streams[stream]
        )
        prefetch = min(used_words - 1, 7) if first and len(streams[stream]) > 1 else 0
        words[address * 3] = words[address * 3] & 0xC7FFFFFF | prefetch << 27

        raw_swizzle = words[address * 3 + 1] & 0xFFF
        declaration_swizzle = [(element_type >> (10 + component * 3)) & 7
                               for component in range(4)]
        if ((element_type >> 6) & 3) == 1 and vertex_format in (25, 26, 31, 32):
            declaration_swizzle[0], declaration_swizzle[1] = declaration_swizzle[1], declaration_swizzle[0]
            declaration_swizzle[2], declaration_swizzle[3] = declaration_swizzle[3], declaration_swizzle[2]
        swizzle = 0
        for component in range(4):
            source = raw_swizzle >> (component * 3) & 7
            swizzle |= (declaration_swizzle[source] if source < 4 else source) << (component * 3)
        words[address * 3 + 1] = (
            words[address * 3 + 1] & 0x80000000
            | swizzle
            | ((element_type >> 8) & 1) << 12
            | ((element_type >> 9) & 1) << 13
            | vertex_format << 16
            | (not first) << 30
        )
        words[address * 3 + 2] = (
            words[address * 3 + 2] & 0x80000000
            | strides[stream] // 4
            | byte_offset // 4 << 8
        )
    return struct.pack(f">{len(words)}I", *words)


def extract(game_root: Path, output: Path, binary_dir: Path | None = None,
            archive_extractor: Path | None = None) -> dict:
    shader_root = game_root / "media" / "shaders"
    if not shader_root.is_dir():
        raise ValueError(f"FH1 shader directory is unavailable: {shader_root}")

    entries: dict[tuple[str, str], dict] = {}
    binaries: dict[tuple[str, str], bytes] = {}
    declarations = set()
    vertex_sources = []
    container_count = 0

    def add_shader(stage: str, code: bytes, interpolator_count: int, source: dict,
                   generated: bool = False) -> None:
        digest = hashlib.sha256(code).hexdigest().upper()
        key = stage, digest
        entry = entries.setdefault(
            key,
            {
                "stage": stage,
                "sha256": digest,
                "bytes": len(code),
                "interpolator_counts": [],
                "sources": [],
            },
        )
        if interpolator_count not in entry["interpolator_counts"]:
            entry["interpolator_counts"].append(interpolator_count)
            entry["interpolator_counts"].sort()
        if len(entry["sources"]) < 4:
            if generated:
                source = {**source, "asset_derived_vertex_variant": True}
            entry["sources"].append(source)
        binaries.setdefault(key, code)

    def extract_source(source: str, data: bytes) -> None:
        nonlocal container_count
        declarations.update(extract_declarations(data))
        offset = 0
        while offset + CONTAINER.size <= len(data):
            (flags, virtual_size, physical_size, _, constant_table_offset,
             _, shader_offset, field_1c, field_20) = CONTAINER.unpack_from(data, offset)
            container_size = virtual_size + physical_size
            valid = (
                flags & FLAGS_MASK == FLAGS_MAGIC
                and container_size >= CONTAINER.size
                and container_size <= len(data) - offset
                and constant_table_offset != 0
                and field_1c == 0
                and field_20 == 0
                and shader_offset + SHADER.size <= virtual_size
            )
            if not valid:
                offset += 4
                continue

            physical_offset, shader_size, _, _, _, interpolator_info = SHADER.unpack_from(
                data, offset + shader_offset
            )
            valid = (
                shader_size != 0
                and shader_size % 12 == 0
                and physical_offset <= physical_size
                and shader_size <= physical_size - physical_offset
            )
            if not valid:
                offset += 4
                continue

            stage = "vertex" if flags & 1 else "pixel"
            code_offset = offset + virtual_size + physical_offset
            code = data[code_offset : code_offset + shader_size]
            interpolator_count = (interpolator_info >> 5) & 0x1F
            source_info = {
                "path": source,
                "container_offset": offset,
                "ucode_offset": code_offset,
            }
            add_shader(stage, code, interpolator_count, source_info)
            if stage == "vertex" and shader_offset + VERTEX_SHADER.size <= virtual_size:
                vertex_shader = VERTEX_SHADER.unpack_from(data, offset + shader_offset)
                element_start, element_count = vertex_shader[6:8]
                metadata_count = element_start + element_count
                if (metadata_count <=
                        (virtual_size - shader_offset - VERTEX_SHADER.size) // 4):
                    metadata = struct.unpack_from(
                        f">{metadata_count}I", data,
                        offset + shader_offset + VERTEX_SHADER.size,
                    )
                    shader_elements = tuple(
                        (value & 0xFFF, value >> 12 & 0xF, value >> 16 & 0xF)
                        for value in metadata[element_start : element_start + element_count]
                    )
                    vertex_sources.append(
                        (code, shader_elements, interpolator_count, source_info)
                    )
            container_count += 1
            offset += container_size

    for source in sorted(shader_root.rglob("*.fxobj")):
        extract_source(source.relative_to(game_root).as_posix(), source.read_bytes())

    # FH1's method-21 track archives are XMem LZX streams without local ZIP
    # headers. The small native helper reuses ReXGlue's existing LZX decoder.
    if archive_extractor is not None and not archive_extractor.is_file():
        raise ValueError(f"FH1 archive extractor is unavailable: {archive_extractor}")
    with tempfile.TemporaryDirectory() as temporary:
        extracted = Path(temporary) / "shader.fxobj"
        for archive in sorted((game_root / "media").rglob("*.zip")):
            with ZipFile(archive) as zipped:
                for member in sorted(zipped.infolist(), key=lambda item: item.filename):
                    if member.is_dir() or not member.filename.lower().endswith(".fxobj"):
                        continue
                    if member.compress_type == 21:
                        if archive_extractor is None:
                            raise ValueError(
                                f"FH1 method-21 shader archive requires --archive-extractor: "
                                f"{archive}!/{member.filename}"
                            )
                        result = subprocess.run(
                            [archive_extractor, archive, str(member.header_offset),
                             str(member.compress_size), str(member.file_size), extracted],
                            capture_output=True, text=True,
                        )
                        if result.returncode:
                            raise ValueError(
                                f"failed to extract {archive}!/{member.filename}: "
                                f"{result.stderr.strip()}"
                            )
                        data = extracted.read_bytes()
                    else:
                        data = zipped.read(member)
                    source = (
                        f"{archive.relative_to(game_root).as_posix()}!/{member.filename}"
                    )
                    extract_source(source, data)

    raw_shader_count = len(entries)
    for code, shader_elements, interpolator_count, source in vertex_sources:
        for declaration in declarations:
            variant = patch_vertex_shader(code, shader_elements, declaration)
            if variant is not None and variant != code:
                add_shader("vertex", variant, interpolator_count, source, True)

    if not entries:
        raise ValueError("no FH1 Xenos shader containers were found")

    manifest = {
        "schema": "pinyon-shift.fh1-disc-shader-corpus.v1",
        "title_id": "4D5309C9",
        "container_count": container_count,
        "raw_shader_count": raw_shader_count,
        "vertex_declaration_count": len(declarations),
        "asset_derived_vertex_variant_count": len(entries) - raw_shader_count,
        "shader_count": len(entries),
        "entries": [entries[key] for key in sorted(entries)],
    }
    if binary_dir is not None:
        binary_dir.mkdir(parents=True, exist_ok=True)
        for key in sorted(entries):
            entry = entries[key]
            count = max(entry["interpolator_counts"])
            destination = binary_dir / f"{entry['stage']}-i{count:02d}-{entry['sha256']}.bin"
            destination.write_bytes(binaries[key])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract FH1 retail Xenos shader microcode for local offline translation."
    )
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--binary-dir", type=Path)
    parser.add_argument("--archive-extractor", type=Path)
    args = parser.parse_args()
    try:
        manifest = extract(args.game_root.resolve(), args.output.resolve(),
                           args.binary_dir.resolve() if args.binary_dir else None,
                           args.archive_extractor.resolve() if args.archive_extractor else None)
    except (BadZipFile, OSError, ValueError) as error:
        parser.error(str(error))
    print(
        f"extracted {manifest['shader_count']} unique FH1 shaders from "
        f"{manifest['container_count']} containers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
