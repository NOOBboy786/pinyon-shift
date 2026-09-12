#!/usr/bin/env python3
"""Catalog FH1 UI archives without putting game-derived data in the repo."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


LOCAL_HEADER = struct.Struct("<IHHHHHIIIHH")
LOCAL_HEADER_SIGNATURE = 0x04034B50
SUPPORTED_METHODS = {0, 21}
DEFAULT_ARCHIVES = (
    "media/UI.zip",
    "media/ui/Fonts.zip",
    "media/ui/Textures.zip",
    "media/ui/textures/Horizon.zip",
)
SCENE_PATH = re.compile(r"(?:^|/)Scenes/ui4/([^/]+)\.(bgf|bsg|fbf)$", re.IGNORECASE)
ASSET_REFERENCE = re.compile(
    rb"(?i)(?:game|update):\\[^\x00\r\n]{1,240}|"
    rb"[A-Za-z0-9_ ./\\-]{2,180}\.(?:xds|tga|bgf|bsg|fbf|dt|xml|lua)"
)


class UiInspectionError(ValueError):
    """A malformed archive or unsupported requested extraction."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_range(archive: Path, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0:
        raise UiInspectionError("archive range is negative")
    file_size = archive.stat().st_size
    if offset > file_size or size > file_size - offset:
        raise UiInspectionError(
            f"archive range is outside {archive}: offset={offset} size={size}"
        )
    with archive.open("rb") as stream:
        stream.seek(offset)
        data = stream.read(size)
    if len(data) != size:
        raise UiInspectionError(f"truncated archive range in {archive}")
    return data


def payload_offset(archive: Path, offset: int, mode: str = "auto") -> int:
    """Resolve a local-header or already-resolved payload offset.

    The native XMem helper consumes compressed payload bytes. Some callers have
    a ZipInfo local-header offset, while extraction manifests may already store
    the payload offset, so support both forms explicitly.
    """
    if mode not in {"auto", "header", "payload"}:
        raise UiInspectionError(f"invalid payload offset mode: {mode}")
    if mode == "payload":
        return offset
    signature = _read_range(archive, offset, 4)
    if struct.unpack("<I", signature)[0] != LOCAL_HEADER_SIGNATURE:
        if mode == "header":
            raise UiInspectionError(f"missing ZIP local header at offset {offset}")
        return offset
    fields = LOCAL_HEADER.unpack(_read_range(archive, offset, LOCAL_HEADER.size))
    name_size, extra_size = fields[9], fields[10]
    resolved = offset + LOCAL_HEADER.size + name_size + extra_size
    _read_range(archive, resolved, 0)
    return resolved


def scene_family(name: str) -> str | None:
    match = SCENE_PATH.search(name.replace("\\", "/"))
    return match.group(1) if match else None


def _decode_reference(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").rstrip("\x00")


def asset_references(data: bytes, limit: int = 256) -> list[str]:
    values = {_decode_reference(match) for match in ASSET_REFERENCE.findall(data)}
    return sorted(values, key=str.casefold)[:limit]


def extract_entry(
    archive: Path,
    info,
    helper: Path | None,
    offset_mode: str,
    maximum_size: int,
) -> bytes:
    if info.file_size > maximum_size:
        raise UiInspectionError(
            f"entry is larger than the extraction limit: {info.filename}"
        )
    if info.compress_type == 0:
        with ZipFile(archive) as zipped:
            data = zipped.read(info)
    elif info.compress_type == 21:
        if helper is None:
            raise UiInspectionError(
                f"method-21 entry requires --archive-extractor: {info.filename}"
            )
        if not helper.is_file():
            raise UiInspectionError(f"archive extractor does not exist: {helper}")
        with tempfile.TemporaryDirectory(prefix="fh1-ui-") as temporary:
            output = Path(temporary) / "entry.bin"
            offset = payload_offset(archive, info.header_offset, offset_mode)
            command = [
                str(helper),
                str(archive),
                str(offset),
                str(info.compress_size),
                str(info.file_size),
                str(output),
            ]
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise UiInspectionError(
                    f"failed to extract {info.filename}: {detail or 'helper failed'}"
                )
            try:
                data = output.read_bytes()
            except OSError as error:
                raise UiInspectionError(
                    f"archive extractor produced no output for {info.filename}"
                ) from error
    else:
        raise UiInspectionError(
            f"unsupported compression method {info.compress_type} for {info.filename}"
        )
    if len(data) != info.file_size:
        raise UiInspectionError(
            f"size mismatch for {info.filename}: got {len(data)}, expected {info.file_size}"
        )
    if (zlib.crc32(data) & 0xFFFFFFFF) != info.CRC:
        raise UiInspectionError(f"CRC mismatch for {info.filename}")
    return data


def parse_fontmap(data: bytes) -> dict[str, object]:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise UiInspectionError(f"fontmap.xml is not valid XML: {error}") from error
    mappings = [
        {"fontname": item.attrib["fontname"], "target": item.attrib["target"]}
        for item in root.findall("mapping")
        if "fontname" in item.attrib and "target" in item.attrib
    ]
    fallbacks = [
        {
            key: item.attrib[key]
            for key in ("lang", "font", "threshold", "scale_fc", "gap")
            if key in item.attrib
        }
        for item in root.findall("fallback_adjuster")
        if item.attrib.get("lang") and item.attrib.get("font")
    ]
    return {"mappings": mappings, "fallback_adjusters": fallbacks}


def _matches(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def _entry_record(archive: Path, info, offset_mode: str) -> dict[str, object]:
    offset = payload_offset(archive, info.header_offset, offset_mode)
    compressed = _read_range(archive, offset, info.compress_size)
    return {
        "name": info.filename,
        "method": info.compress_type,
        "compressed_size": info.compress_size,
        "uncompressed_size": info.file_size,
        "crc32": f"{info.CRC:08x}",
        "compressed_sha256": sha256_bytes(compressed),
        "header_offset": info.header_offset,
        "payload_offset": offset,
        "scene_family": scene_family(info.filename),
    }


def inspect(
    game_root: Path,
    output: Path,
    archives: list[Path],
    helper: Path | None = None,
    patterns: list[str] | None = None,
    offset_mode: str = "auto",
    maximum_size: int = 32 * 1024 * 1024,
) -> dict[str, object]:
    patterns = list(patterns or [])
    resolved_output = output.resolve()
    if ".local" not in {part.casefold() for part in resolved_output.parts}:
        raise UiInspectionError("derived output must be below a .local directory")
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    fontmap: dict[str, object] | None = None
    warnings: list[str] = []
    for archive in archives:
        archive = archive.resolve()
        if not archive.is_file():
            warnings.append(f"missing archive: {archive}")
            continue
        archive_record: dict[str, object] = {
            "path": archive.as_posix(),
            "size": archive.stat().st_size,
            "sha256": sha256_file(archive),
            "entries": [],
        }
        try:
            with ZipFile(archive) as zipped:
                for info in sorted(zipped.infolist(), key=lambda item: item.filename.casefold()):
                    record = _entry_record(archive, info, offset_mode)
                    requested = _matches(info.filename, patterns)
                    auto_fontmap = info.filename.casefold() == "fontmap.xml"
                    if (requested or auto_fontmap) and not info.is_dir():
                        can_extract = info.compress_type == 0 or helper is not None
                        if not can_extract:
                            if requested:
                                raise UiInspectionError(
                                    f"compression method {info.compress_type} requires --archive-extractor for {info.filename}"
                                )
                            warnings.append(
                                f"skipped automatic fontmap extraction without --archive-extractor: {archive.name}"
                            )
                            record["extracted"] = False
                        else:
                            data = extract_entry(archive, info, helper, offset_mode, maximum_size)
                            record["sha256"] = sha256_bytes(data)
                            record["asset_references"] = asset_references(data)
                            record["extracted"] = True
                            if auto_fontmap:
                                fontmap = parse_fontmap(data)
                    else:
                        record["extracted"] = False
                    archive_record["entries"].append(record)
        except (BadZipFile, OSError, UiInspectionError) as error:
            raise UiInspectionError(f"{archive}: {error}") from error
        records.append(archive_record)
    result = {
        "schema_version": 1,
        "game_root": game_root.resolve().as_posix(),
        "archives": records,
        "fontmap": fontmap or {"mappings": [], "fallback_adjusters": []},
        "extract_patterns": patterns,
        "warnings": warnings,
    }
    resolved_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _default_archives(game_root: Path) -> list[Path]:
    return [game_root / relative for relative in DEFAULT_ARCHIVES if (game_root / relative).is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", action="append", type=Path, help="archive relative to --game-root; repeatable")
    parser.add_argument("--archive-extractor", type=Path)
    parser.add_argument("--extract-pattern", action="append", default=[], help="member glob to extract and inspect; repeatable")
    parser.add_argument("--offset-mode", choices=("auto", "header", "payload"), default="auto")
    parser.add_argument("--maximum-entry-size", type=int, default=32 * 1024 * 1024)
    args = parser.parse_args()
    try:
        game_root = args.game_root.resolve()
        archives = [
            path if path.is_absolute() else game_root / path
            for path in (args.archive or _default_archives(game_root))
        ]
        result = inspect(
            game_root,
            args.output,
            archives,
            args.archive_extractor,
            args.extract_pattern,
            args.offset_mode,
            args.maximum_entry_size,
        )
    except (OSError, UiInspectionError, ValueError) as error:
        parser.error(str(error))
    print(
        f"Inspected {len(result['archives'])} archive(s); "
        f"wrote {args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
