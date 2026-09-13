#!/usr/bin/env python3
"""Re-encode one authored UI4 scene member for the UI-14 stream route.

The pause screen is built from ``GAME:\\Media\\UI\\Scenes\\UI4\\
925_PAUSE_MENU.bgf``.  The title's item deserializer (``sub_82F26560``) walks
one length-prefixed item section whose loop count is
``*(section+16) + *(section+20)`` and whose byte length is an equality check
against the 4-byte declaration in front of the items.  The item count is not a
stream value: the two words are copied out of the member's fixed header at
offsets ``0x24``/``0x28`` (element and wrapper item counts), so an extra item
needs the declaration, the two header words and the item bytes to change
together.  Feeding a longer member at the loader boundary therefore requires
this bounded re-encoder, not an in-place payload patch.

The tool parses the section strictly (a parse that does not consume exactly the
declared length is rejected, never guessed at), rebuilds the section from the
parsed item slices, and only then duplicates one wrapper+element pair.  A
no-change run must reproduce its input byte for byte; ``--check-roundtrip``
asserts that before any modification is written.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Iterable

MARKER = b"AnarkBGF"
MARKER_OFFSET = 6
HEADER_RECORD_LENGTH = 0x1A
ITEM_HEADER_BYTES = 14
WRAPPER_EXTRA_BYTES = 5
PROPERTY_STRIDE = 8
MAXIMUM_ITEMS = 8192
MAXIMUM_PROPERTIES = 512
# Header words the deserializer copies into the section at +16/+20.  The file
# stores the pair twice; both copies are kept consistent.
ELEMENT_COUNT_OFFSET = 0x24
WRAPPER_COUNT_OFFSET = 0x28
ELEMENT_COUNT_REPEAT_OFFSET = 0x70
WRAPPER_COUNT_REPEAT_OFFSET = 0x74
# Contract hash of the seven pause rows' element records (PAUSE_MENU_BUTTON).
PAUSE_ROW_CONTRACT = 0xBDF05338
# Wrapper name hashes of the seven authored pause rows.
PAUSE_ROW_NAMES = (
    0x22352942,
    0x22362981,
    0x223729C0,
    0x223829FF,
    0x22392A3E,
    0x223A2A7D,
    0x223B2ABC,
)


class SceneInsertError(ValueError):
    """The member does not match the verified pause-item stream format."""


def u32be(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise SceneInsertError(f"word at {offset:#x} is outside the member")
    return struct.unpack_from(">I", data, offset)[0]


def put_u32be(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into(">I", data, offset, value & 0xFFFFFFFF)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclasses.dataclass(frozen=True)
class Item:
    start: int
    end: int
    name: int
    parent: int
    value: int
    kind: int
    flags: int
    properties: tuple[tuple[int, int], ...]

    @property
    def wrapper(self) -> bool:
        return bool(self.flags & 0x04)

    @property
    def size(self) -> int:
        return self.end - self.start


@dataclasses.dataclass(frozen=True)
class Section:
    start: int
    declared: int
    items: tuple[Item, ...]

    @property
    def end(self) -> int:
        return self.start + 4 + self.declared

    @property
    def elements(self) -> int:
        return sum(1 for item in self.items if not item.wrapper)

    @property
    def wrappers(self) -> int:
        return sum(1 for item in self.items if item.wrapper)


def parse_item(data: bytes, start: int) -> Item:
    """Parse one item record; reject anything the deserializer cannot walk."""
    limit = len(data)
    if start + ITEM_HEADER_BYTES > limit:
        raise SceneInsertError(f"item at {start:#x} runs past the member")
    name = u32be(data, start)
    parent = u32be(data, start + 4)
    value = u32be(data, start + 8)
    kind = data[start + 12]
    flags = data[start + 13]
    cursor = start + ITEM_HEADER_BYTES
    if flags & 0x04:
        cursor += WRAPPER_EXTRA_BYTES
    if cursor + 4 > limit:
        raise SceneInsertError(f"item at {start:#x} truncates before its count")
    count = u32be(data, cursor)
    cursor += 4
    if count > MAXIMUM_PROPERTIES:
        raise SceneInsertError(
            f"item at {start:#x} declares {count} properties, beyond "
            f"{MAXIMUM_PROPERTIES}"
        )
    end = cursor + count * PROPERTY_STRIDE
    if end > limit:
        raise SceneInsertError(f"item at {start:#x} runs past the member")
    properties = tuple(
        (u32be(data, cursor + index * PROPERTY_STRIDE),
         u32be(data, cursor + index * PROPERTY_STRIDE + 4))
        for index in range(count)
    )
    return Item(start, end, name, parent, value, kind, flags, properties)


def parse_section(data: bytes, start: int) -> Section:
    """Parse one item section; the items must consume the declared length."""
    if start < 0 or start + 4 > len(data):
        raise SceneInsertError(f"section at {start:#x} is outside the member")
    declared = u32be(data, start)
    end = start + 4 + declared
    if declared == 0 or end > len(data):
        raise SceneInsertError(
            f"section at {start:#x} declares {declared} bytes past the member"
        )
    items: list[Item] = []
    cursor = start + 4
    while cursor < end:
        if len(items) >= MAXIMUM_ITEMS:
            raise SceneInsertError(
                f"section at {start:#x} exceeds {MAXIMUM_ITEMS} items"
            )
        item = parse_item(data, cursor)
        if item.end > end:
            raise SceneInsertError(
                f"item at {cursor:#x} overruns the declared section length"
            )
        items.append(item)
        cursor = item.end
    if cursor != end:
        raise SceneInsertError(f"section at {start:#x} does not end cleanly")
    return Section(start, declared, tuple(items))


def find_pause_section(data: bytes) -> Section:
    """Locate the unique item section that carries the seven pause rows."""
    if data[:4] != b"\x01\x04\x00\x00" or data[MARKER_OFFSET:MARKER_OFFSET + 8] != MARKER:
        raise SceneInsertError("member does not start with the AnarkBGF header")
    if u32be(data, 2) != HEADER_RECORD_LENGTH:
        raise SceneInsertError("member header record length is not 0x1A")
    candidates: list[Section] = []
    errors: list[str] = []
    for start in range(0x20, len(data) - 4):
        try:
            section = parse_section(data, start)
        except SceneInsertError as error:
            errors.append(str(error))
            continue
        names = {item.name for item in section.items if item.wrapper}
        if set(PAUSE_ROW_NAMES) <= names:
            candidates.append(section)
    if len(candidates) != 1:
        raise SceneInsertError(
            f"expected exactly one item section with the seven pause rows, "
            f"found {len(candidates)}"
        )
    section = candidates[0]
    rows = [item for item in section.items if item.name in PAUSE_ROW_NAMES]
    for item in rows:
        position = section.items.index(item)
        following = section.items[position + 1]
        if following.wrapper or following.parent != position:
            raise SceneInsertError(
                f"row wrapper {item.name:#010x} is not followed by its element"
            )
    return section


def pause_row_pairs(section: Section) -> list[tuple[int, Item, Item]]:
    """Return (row index, wrapper, element) for the seven authored rows."""
    pairs: list[tuple[int, Item, Item]] = []
    for index, item in enumerate(section.items):
        if not item.wrapper or item.name not in PAUSE_ROW_NAMES:
            continue
        element = section.items[index + 1]
        if element.parent != index:
            raise SceneInsertError(
                f"row {item.name:#010x} element parent is {element.parent:#x}, "
                f"expected {index:#x}"
            )
        if element.name != PAUSE_ROW_CONTRACT:
            raise SceneInsertError(
                f"row {item.name:#010x} next record is {element.name:#010x}, "
                "not the pause button contract"
            )
        pairs.append((PAUSE_ROW_NAMES.index(item.name), item, element))
    if len(pairs) != len(PAUSE_ROW_NAMES):
        raise SceneInsertError(
            f"found {len(pairs)} pause row pairs, expected {len(PAUSE_ROW_NAMES)}"
        )
    return pairs


def rebuild(section: Section, data: bytes, items: Iterable[Item], declared: int) -> bytes:
    """Re-serialize the section from its parsed item slices."""
    body = b"".join(data[item.start:item.end] for item in items)
    if len(body) != declared:
        raise SceneInsertError("rebuilt item body does not match its declaration")
    return data[:section.start] + struct.pack(">I", declared) + body + data[section.end:]


def encode(data: bytes, row_index: int) -> tuple[bytes, dict]:
    """Return the re-encoded member plus a summary of every change made."""
    section = find_pause_section(data)
    pairs = pause_row_pairs(section)
    if not 0 <= row_index < len(pairs):
        raise SceneInsertError(
            f"row index {row_index} is outside the seven authored rows"
        )

    counts = (section.elements, section.wrappers)
    if section.declared != sum(item.size for item in section.items):
        raise SceneInsertError("section length is not the sum of its items")
    for offset, expected in (
        (ELEMENT_COUNT_OFFSET, counts[0]),
        (WRAPPER_COUNT_OFFSET, counts[1]),
    ):
        found = u32be(data, offset)
        if found != expected:
            raise SceneInsertError(
                f"header word at {offset:#x} is {found}, expected the parsed "
                f"item count {expected}"
            )
    for offset, source in (
        (ELEMENT_COUNT_REPEAT_OFFSET, ELEMENT_COUNT_OFFSET),
        (WRAPPER_COUNT_REPEAT_OFFSET, WRAPPER_COUNT_OFFSET),
    ):
        if u32be(data, offset) != u32be(data, source):
            raise SceneInsertError(
                f"header word at {offset:#x} does not mirror {source:#x}"
            )

    # A no-change rebuild must be byte-identical to the input.
    roundtrip = rebuild(section, data, section.items, section.declared)
    if roundtrip != data:
        raise SceneInsertError("no-change roundtrip does not reproduce the input")

    _, wrapper, element = pairs[row_index]
    position = section.items.index(wrapper)
    new_wrapper_index = len(section.items)
    inserted = bytearray(data[wrapper.start:element.end])
    element_offset = element.start - wrapper.start
    # The element's parent index is the created-record index of the wrapper that
    # owns it; the copy belongs to the appended wrapper, not the source row.
    put_u32be(inserted, element_offset + 4, new_wrapper_index)

    declared = section.declared + len(inserted)
    items = list(section.items)
    items.append(dataclasses.replace(wrapper, start=wrapper.start + len(inserted)))
    items.append(
        dataclasses.replace(
            element,
            start=element.start + len(inserted),
            parent=new_wrapper_index,
        )
    )
    body = (
        b"".join(data[item.start:item.end] for item in section.items)
        + bytes(inserted)
    )
    if len(body) != declared:
        raise SceneInsertError("patched item body does not match its declaration")
    patched = bytearray(
        data[:section.start]
        + struct.pack(">I", declared)
        + body
        + data[section.end:]
    )
    for offset in (
        ELEMENT_COUNT_OFFSET,
        ELEMENT_COUNT_REPEAT_OFFSET,
    ):
        put_u32be(patched, offset, u32be(data, offset) + 1)
    for offset in (
        WRAPPER_COUNT_OFFSET,
        WRAPPER_COUNT_REPEAT_OFFSET,
    ):
        put_u32be(patched, offset, u32be(data, offset) + 1)

    summary = {
        "input_bytes": len(data),
        "output_bytes": len(patched),
        "input_sha256": sha256(data),
        "output_sha256": sha256(bytes(patched)),
        "section_offset": section.start,
        "section_declared_before": section.declared,
        "section_declared_after": declared,
        "items_before": len(section.items),
        "items_after": len(section.items) + 2,
        "elements_before": counts[0],
        "wrappers_before": counts[1],
        "elements_after": counts[0] + 1,
        "wrappers_after": counts[1] + 1,
        "insert_offset": section.end,
        "insert_bytes": len(inserted),
        "row_index": row_index,
        "row_name": f"{wrapper.name:#010x}",
        "source_wrapper_index": position,
        "new_wrapper_index": new_wrapper_index,
    }
    return bytes(patched), summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--row-index", type=int, default=0)
    parser.add_argument(
        "--check-roundtrip",
        action="store_true",
        help="parse, verify the no-change roundtrip and print the summary only",
    )
    parser.add_argument("--json", type=Path, help="write the summary as JSON")
    arguments = parser.parse_args(argv)

    data = arguments.input.read_bytes()
    try:
        if arguments.check_roundtrip:
            section = find_pause_section(data)
            pause_row_pairs(section)
            rebuilt = rebuild(section, data, section.items, section.declared)
            if rebuilt != data:
                raise SceneInsertError(
                    "no-change roundtrip does not reproduce the input"
                )
            summary = {
                "roundtrip": "identical",
                "input_bytes": len(data),
                "input_sha256": sha256(data),
                "section_offset": section.start,
                "section_declared": section.declared,
                "items": len(section.items),
                "elements": section.elements,
                "wrappers": section.wrappers,
                "rows": [
                    {"index": index, "name": f"{wrapper.name:#010x}"}
                    for index, wrapper, _ in pause_row_pairs(section)
                ],
            }
        else:
            patched, summary = encode(data, arguments.row_index)
            if arguments.output is None:
                raise SceneInsertError("--output is required to write the member")
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_bytes(patched)
            summary["output"] = str(arguments.output)
    except SceneInsertError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    text = json.dumps(summary, indent=2, sort_keys=True)
    print(text)
    if arguments.json is not None:
        arguments.json.parent.mkdir(parents=True, exist_ok=True)
        arguments.json.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
