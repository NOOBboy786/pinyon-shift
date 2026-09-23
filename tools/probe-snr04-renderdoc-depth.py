"""Read all depth samples before/after one draw through qrenderdoc --python."""

import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import traceback

import renderdoc as rd

capture = Path(os.environ['SNR04_CAPTURE'])
out = Path(os.environ['SNR04_OUTPUT'])
event = int(os.environ['SNR04_EVENT'])
state = {'stage': 'open', 'capture': capture.name, 'event': event}


def save():
    out.write_text(json.dumps(state))


cap = replay = None
try:
    save()
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(str(capture), 'rdc', None)
    if 'Success' not in str(result):
        raise RuntimeError(str(result))
    result, replay = cap.OpenCapture(rd.ReplayOptions(), None)
    if 'Success' not in str(result):
        raise RuntimeError(str(result))
    replay.SetFrameEvent(event, True)
    pipeline = replay.GetPipelineState()
    target = pipeline.GetDepthTarget()
    texture = next(t for t in replay.GetTextures()
                   if t.resourceId == target.resource)
    viewport = pipeline.GetViewport(0)
    state.update(stage='read', depth_resource=str(target.resource),
                 format=texture.format.Name(), width=texture.width,
                 height=texture.height, samples=texture.msSamp,
                 viewport=[viewport.x, viewport.y, viewport.width,
                           viewport.height, viewport.minDepth, viewport.maxDepth])
    save()
    assert state['format'] == 'D32S8_TYPELESS' and texture.msSamp == 4
    subresource = rd.Subresource()
    subresource.mip = target.firstMip
    subresource.slice = target.firstSlice
    state['sample_details'] = []
    coverage = bytearray(texture.width * texture.height)
    for sample in range(texture.msSamp):
        subresource.sample = sample
        data = []
        detail = {'sample': sample}
        for label, frame_event in (('before', event - 1), ('after', event)):
            replay.SetFrameEvent(frame_event, True)
            value = bytes(replay.GetTextureData(target.resource, subresource))
            assert len(value) == texture.width * texture.height * 8
            suffix = '' if sample == 0 else f'-s{sample}'
            (out.parent / f'{out.stem}-{label}{suffix}.depth').write_bytes(value)
            detail[label] = {'bytes': len(value),
                             'sha256': hashlib.sha256(value).hexdigest()}
            data.append(value)
        changes = [i for i in range(texture.width * texture.height)
                   if data[0][i * 8:i * 8 + 4] != data[1][i * 8:i * 8 + 4]]
        for pixel in changes:
            coverage[pixel] |= 1 << sample
        detail['changed_depth_samples'] = len(changes)
        detail['changed_depth_range'] = [
            min(struct.unpack_from('<f', data[1], i * 8)[0] for i in changes),
            max(struct.unpack_from('<f', data[1], i * 8)[0] for i in changes)] if changes else []
        state['sample_details'].append(detail)
        if sample == 0:
            state['before'], state['after'] = detail['before'], detail['after']
            state['changed_texels_sample0'] = len(changes)
            state['changed_depth_range_sample0'] = detail['changed_depth_range']
    coverage_path = out.parent / f'{out.stem}-coverage.u8'
    coverage_path.write_bytes(coverage)
    state['coverage'] = {'bytes': len(coverage),
                         'sha256': hashlib.sha256(coverage).hexdigest(),
                         'pixels': sum(bool(mask) for mask in coverage),
                         'samples': sum(bin(mask).count('1') for mask in coverage)}
    state['stage'] = 'done'
    save()
except Exception:
    state.update(stage='error', error=traceback.format_exc())
    save()
finally:
    if replay:
        replay.Shutdown()
    if cap:
        cap.Shutdown()
sys.exit(0)
