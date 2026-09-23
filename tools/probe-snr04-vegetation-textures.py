"""Trace selected vegetation pixel textures to their latest captured producer.

Run with qrenderdoc --python and SNR04_CAPTURE, SNR04_OUTPUT, SNR04_EVENT.
"""

import json
import os
from pathlib import Path
import traceback

import renderdoc as rd


capture = Path(os.environ["SNR04_CAPTURE"])
output = Path(os.environ["SNR04_OUTPUT"])
event = int(os.environ.get("SNR04_EVENT", "11206"))
state = {"capture": capture.name, "event": event, "stage": "open"}
cap = replay = None
try:
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(str(capture), "rdc", None)
    if "Success" not in str(result):
        raise RuntimeError(str(result))
    result, replay = cap.OpenCapture(rd.ReplayOptions(), None)
    if "Success" not in str(result):
        raise RuntimeError(str(result))
    replay.SetFrameEvent(event, True)
    pipeline = replay.GetPipelineState()
    viewport = pipeline.GetViewport(0)
    state["viewport"] = [viewport.width, viewport.height]
    used = pipeline.GetReadOnlyResources(rd.ShaderStage.Pixel)
    state["pixel_binding_count"] = len(used)
    assert len(used) == 2, "selected draw must have two pixel textures"
    textures = {texture.resourceId: texture for texture in replay.GetTextures()}
    state["pixel_textures"] = []
    for index, binding in enumerate(used):
        texture = textures[binding.descriptor.resource]
        state["pixel_textures"].append({
            "binding_order": index,
            "resource": str(texture.resourceId),
            "width": texture.width,
            "height": texture.height,
            "format": texture.format.Name(),
            "mips": texture.mips,
            "samples": texture.msSamp,
        })
    full_view = [binding.descriptor.resource for binding in used
                 if textures[binding.descriptor.resource].width == viewport.width
                 and textures[binding.descriptor.resource].height == viewport.height]
    assert len(full_view) == 1, "no unique viewport-sized pixel texture"
    target = full_view[0]
    copies = [usage.eventId for usage in replay.GetUsage(target)
              if usage.eventId < event and str(usage.usage) == "ResourceUsage.CopyDst"]
    assert copies, "viewport-sized texture has no captured copy producer"
    copy_event = max(copies)
    actions = {}

    def visit(nodes):
        for action in nodes:
            actions[action.eventId] = action
            visit(action.children)

    visit(replay.GetRootActions())
    copy = actions[copy_event]
    assert copy.copyDestination == target
    source = copy.copySource
    buffer = next(buffer for buffer in replay.GetBuffers()
                  if buffer.resourceId == source)
    writes = [usage.eventId for usage in replay.GetUsage(source)
              if usage.eventId < copy_event
              and str(usage.usage) == "ResourceUsage.CS_RWResource"]
    assert writes, "copy source has no captured compute write"
    state["full_view_producer"] = {
        "texture": str(target),
        "copy_event": copy_event,
        "copy_source": str(source),
        "copy_source_buffer_bytes": buffer.length,
        "last_compute_write_event": max(writes),
    }
    state["stage"] = "done"
except Exception:
    state.update(stage="error", error=traceback.format_exc())
finally:
    output.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    if replay:
        replay.Shutdown()
    if cap:
        cap.Shutdown()
