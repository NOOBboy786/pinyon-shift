#!/usr/bin/env python3
"""Report partial depth agreement for one captured vegetation draw."""

import argparse
import json
from pathlib import Path
import statistics
import struct


def check(probe_path, identity_path, depth_path, item):
    probe = json.loads(probe_path.read_text(encoding='utf-8'))
    assert probe['stage'] == 'done' and probe['format'] == 'D32S8_TYPELESS'
    width, height = probe['width'], probe['height']
    before = (probe_path.parent / f'{probe_path.stem}-before.depth').read_bytes()
    after = (probe_path.parent / f'{probe_path.stem}-after.depth').read_bytes()
    assert len(before) == len(after) == width * height * 8
    ppm = identity_path.read_bytes()
    header = ppm.split(b'\n', 3)
    assert header[0] == b'P6' and header[2] == b'255'
    native_width, native_height = map(int, header[1].split())
    assert native_width == width and native_height >= height
    colors = memoryview(ppm)[sum(len(part) + 1 for part in header[:3]):]
    depths = depth_path.read_bytes()
    assert len(colors) == native_width * native_height * 3
    assert len(depths) == native_width * native_height * 4
    changed = overlap = near = 0
    errors = []
    for pixel in range(width * height):
        if before[pixel * 8:pixel * 8 + 8] == after[pixel * 8:pixel * 8 + 8]:
            continue
        changed += 1
        native_id = colors[pixel * 3] | colors[pixel * 3 + 1] << 8
        if native_id != item:
            continue
        overlap += 1
        captured = struct.unpack_from('<f', after, pixel * 8)[0]
        native = struct.unpack_from('<f', depths, pixel * 4)[0]
        error = abs(captured - native)
        near += error < 1e-4
        errors.append(error)
    assert changed == probe['changed_texels_sample0'] and overlap > 0
    return {'event': probe['event'], 'item': item, 'changed_texels_sample0': changed,
            'overlap_texels': overlap, 'within_1e-4': near,
            'median_abs_depth_error': statistics.median(errors),
            'max_abs_depth_error': max(errors),
            'scope': 'sample-0 coordinate overlap; not coverage/depth parity'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe', type=Path)
    parser.add_argument('identity', type=Path)
    parser.add_argument('depth', type=Path)
    parser.add_argument('--item', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.probe, args.identity, args.depth, args.item),
                     sort_keys=True))


if __name__ == '__main__':
    main()
