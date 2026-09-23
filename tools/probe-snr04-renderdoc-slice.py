"""Run with qrenderdoc --python to fingerprint a captured vegetation slice."""

import collections
import hashlib
import json
import os
import struct
import sys
import traceback
from pathlib import Path

import renderdoc as rd

fixture = Path(os.environ['SNR04_FIXTURE']).read_bytes()
capture = Path(os.environ['SNR04_CAPTURE'])
out = Path(os.environ['SNR04_OUTPUT'])
assert fixture[:8] == b'SNR03F1\0'
counts = collections.Counter()
position = 156
for _ in range(struct.unpack_from('<I', fixture, 24)[0]):
    _, _, _, _, _, _, _, vertices, byte_count, _, variants = struct.unpack_from(
        '<6IQ4I', fixture, position)
    counts[vertices] += 1
    position += 48 + 384 + byte_count + variants * 184
assert position == len(fixture)

state = {'stage': 'open', 'capture': capture.name}


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
    actions = [a for a in replay.GetRootActions()
               if a.flags & rd.ActionFlags.Drawcall and a.numIndices in counts]
    state.update(stage='search', candidate_actions=len(actions), matches=[],
                 depth_ranges={})
    save()
    for action in actions:
        replay.SetFrameEvent(action.eventId, True)
        pipeline = replay.GetPipelineState()
        reflection = pipeline.GetShaderReflection(rd.ShaderStage.Vertex)
        if (not reflection or hashlib.sha256(bytes(reflection.rawBytes)).hexdigest()
                != '2adfe080228c468ce9aec7e21d19798fc8aaa32cdba5d7325c4fac4070f21faa'):
            continue
        mesh = replay.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
        assert mesh.numIndices == action.numIndices and mesh.vertexByteStride >= 16
        viewport = pipeline.GetViewport(0)
        depth_range = f'{viewport.minDepth:g}/{viewport.maxDepth:g}'
        state['depth_ranges'][depth_range] = state['depth_ranges'].get(depth_range, 0) + 1
        raw = bytes(replay.GetBufferData(mesh.vertexResourceId, mesh.vertexByteOffset, mesh.vertexByteSize))
        assert len(raw) >= (mesh.numIndices - 1) * mesh.vertexByteStride + 16
        positions = b''.join(raw[i * mesh.vertexByteStride:
                                 i * mesh.vertexByteStride + 16]
                             for i in range(mesh.numIndices))
        state['matches'].append(dict(event=action.eventId,
                                     count=action.numIndices,
                                     postvs=hashlib.sha256(positions).hexdigest()))
        if len(state['matches']) % 10 == 0: save()
    state.update(stage='done')
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
