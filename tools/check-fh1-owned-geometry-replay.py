"""Check every cached layered draw against its GPU source bytes in RenderDoc.

Run with qrenderdoc --python. Set PINYON_SHIFT_RENDERDOC_CAPTURE and
PINYON_SHIFT_RENDERDOC_EXPORT_DIR (a new directory). Cache resource names carry
the source address and size. This checks captured geometry input parity, not
whole-renderer parity or cross-scene mutation coverage.
Optionally set PINYON_SHIFT_GEOMETRY_REFERENCE to a prior successful report to
compare content multisets independently of the current shared-memory copy.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import renderdoc as rd


def flat(actions):
    for action in actions:
        yield action
        yield from flat(action.children)


cap = rd.OpenCaptureFile()
controller = None
out = None
created = False
report = {'draws': [], 'fallback_draws': [], 'copied_bytes': 0}
try:
    out = Path(os.environ['PINYON_SHIFT_RENDERDOC_EXPORT_DIR'])
    out.mkdir(parents=True, exist_ok=False)
    created = True
    capture = Path(os.environ['PINYON_SHIFT_RENDERDOC_CAPTURE'])
    report['capture'] = str(capture.resolve())
    status = cap.OpenFile(str(capture), '', None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    names = {str(r.resourceId): r.name for r in controller.GetResources()}
    shared = [b for b in controller.GetBuffers() if b.length == 1 << 29]
    if len(shared) != 1:
        raise RuntimeError('Expected one 512 MiB shared-memory source')
    source = shared[0].resourceId
    actions = list(flat(controller.GetRootActions()))
    draws = {a.eventId: a for a in actions if a.flags & rd.ActionFlags.Drawcall}
    events = {e.eventId: e for a in actions for e in a.events}
    sd = controller.GetStructuredFile()
    state = {}
    selected = []
    mapped = set()
    for eid, event in sorted(events.items()):
        chunk = sd.chunks[event.chunkIndex]
        params = {chunk.GetChild(i).name: str(chunk.GetChild(i).AsResourceId())
                  for i in range(chunk.NumChildren())
                  if chunk.GetChild(i).type.basetype == rd.SDBasic.Resource}
        cmd = params.get('pCommandList', params.get('CommandList'))
        if chunk.name.endswith('::Reset'):
            state[cmd] = params.get('pInitialState')
        elif chunk.name.endswith('::SetPipelineState'):
            state[cmd] = params['pPipelineState']
        elif chunk.name.endswith(('::ExecuteBundle', '::ClearState', '::ExecuteIndirect')):
            raise RuntimeError('Unsupported command state: ' + chunk.name)
        elif chunk.name.endswith('::CopyBufferRegion'):
            if names.get(params.get('pDstBuffer'), '').startswith('FH1 owned geometry '):
                for i in range(chunk.NumChildren()):
                    child = chunk.GetChild(i)
                    if child.name == 'NumBytes':
                        report['copied_bytes'] += child.data.basic.u
        if eid in draws:
            if not state.get(cmd):
                raise RuntimeError('Missing pipeline state at ' + str(eid))
            mapped.add(eid)
            if names.get(state[cmd]) == 'VS 3BC346726C1C2535, PS 9584B309533EF6C9':
                selected.append((eid, state[cmd]))
    if mapped != set(draws):
        raise RuntimeError('Draw events are missing from the structured stream')
    reference_path = os.environ.get('PINYON_SHIFT_GEOMETRY_REFERENCE')
    reference = None
    if reference_path:
        baseline = json.loads(Path(reference_path).read_text())
        if 'error' in baseline or baseline.get('fallback_draws') or not baseline.get('verified_draws'):
            raise RuntimeError('Reference report is not fully verified')
        reference = Counter((d['bytes'], d['sha256']) for d in baseline['draws'])
        report['reference'] = str(Path(reference_path).resolve())
    report['mapped_draws'] = len(mapped)
    for eid, expected_pipeline in selected:
        controller.SetFrameEvent(eid, True)
        pipeline = controller.GetPipelineState()
        if str(pipeline.GetGraphicsPipelineObject()) != expected_pipeline:
            raise RuntimeError('Pipeline map mismatch at ' + str(eid))
        resources = pipeline.GetReadOnlyResources(rd.ShaderStage.Vertex)
        if len(resources) != 1:
            raise RuntimeError('Unexpected vertex resource count at ' + str(eid))
        descriptor = resources[0].descriptor
        name = names[str(descriptor.resource)]
        if not name.startswith('FH1 owned geometry '):
            if descriptor.resource != source:
                raise RuntimeError('Unknown geometry resource ' + name)
            report['fallback_draws'].append(eid)
            continue
        page_address, page_size = map(int, name.split()[3:])
        if descriptor.byteOffset % 16 or descriptor.byteOffset >= page_size or descriptor.byteSize != page_size - descriptor.byteOffset:
            raise RuntimeError('Unexpected owned SRV extent at ' + str(eid))
        reflection = pipeline.GetShaderReflection(rd.ShaderStage.Vertex)
        index = next(i for i, block in enumerate(reflection.constantBlocks) if block.fixedBindNumber == 3)
        cb = pipeline.GetConstantBlock(rd.ShaderStage.Vertex, index, 0).descriptor
        fetch = struct.unpack('<192I', bytes(controller.GetBufferData(cb.resource, cb.byteOffset, 768)))
        low_offset = fetch[190] & ~3
        size = ((fetch[191] >> 2) & 0xFFFFFF) * 4
        if low_offset >= 16 or not size or low_offset + size > descriptor.byteSize:
            raise RuntimeError('Fetch was not correctly rebased at ' + str(eid))
        offset = descriptor.byteOffset + low_offset
        address = page_address + offset
        actual = bytes(controller.GetBufferData(descriptor.resource, offset, size))
        if len(actual) != size or (reference is None and
                actual != bytes(controller.GetBufferData(source, address, size))):
            raise RuntimeError('Cached geometry differs from source at ' + str(eid))
        report['draws'].append(dict(event=eid, resource=str(descriptor.resource), address=address,
                                   bytes=size, sha256=hashlib.sha256(actual).hexdigest()))
    if not report['draws']:
        raise RuntimeError('No owned geometry draws verified')
    if reference is not None:
        actual_contents = Counter((d['bytes'], d['sha256']) for d in report['draws'])
        report['reference_missing_draws'] = sum((reference - actual_contents).values())
        report['reference_extra_draws'] = sum((actual_contents - reference).values())
        if actual_contents != reference:
            raise RuntimeError('Geometry content multiset differs from reference')
    report['verified_draws'] = len(report['draws'])
    report['distinct_ranges'] = len({(d['address'], d['bytes']) for d in report['draws']})
    report['verified_bytes'] = sum(d['bytes'] for d in report['draws'])
except Exception as error:
    report['error'] = str(error)
finally:
    if controller:
        controller.Shutdown()
    cap.Shutdown()
    if created:
        destination = out / 'geometry-parity.json'
        with destination.open('x') as file:
            json.dump(report, file, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'draws'}, indent=2))
    sys.exit(1 if 'error' in report else 0)
