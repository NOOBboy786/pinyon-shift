"""Trace selected vegetation pixel textures to their latest captured producer.

Run with qrenderdoc --python and SNR04_CAPTURE, SNR04_OUTPUT, SNR04_EVENT.
"""

import json
import hashlib
import os
from pathlib import Path
import re
import struct
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
    cb3 = pipeline.GetConstantBlock(rd.ShaderStage.Pixel, 3, 0).descriptor
    cb3_words = struct.unpack("<8I", bytes(replay.GetBufferData(
        cb3.resource, cb3.byteOffset, 32)))
    assert {binding.access.arrayElement for binding in used} == {
        cb3_words[2], cb3_words[5]}, "pixel descriptors differ from shader indices"
    reflection = pipeline.GetShaderReflection(rd.ShaderStage.Pixel)
    disassembly = replay.DisassembleShader(
        pipeline.GetGraphicsPipelineObject(), reflection, "")
    output.with_suffix(".dxbc.txt").write_bytes(disassembly.encode("utf-8"))
    state["pixel_shader"] = {
        "resource": str(pipeline.GetShader(rd.ShaderStage.Pixel)),
        "descriptor_indices": [cb3_words[2], cb3_words[5]],
        "disassembly_sha256": hashlib.sha256(disassembly.encode()).hexdigest(),
    }
    vertex_disassembly = replay.DisassembleShader(
        pipeline.GetGraphicsPipelineObject(),
        pipeline.GetShaderReflection(rd.ShaderStage.Vertex), "")
    state["vertex_shader"] = {
        "resource": str(pipeline.GetShader(rd.ShaderStage.Vertex)),
        "system_vectors_read": sorted({int(index) for line in vertex_disassembly.splitlines()
                                       if "dcl_constantbuffer" not in line
                                       for index in re.findall(r"CB0\[(\d+)\]", line)}),
    }
    textures = {texture.resourceId: texture for texture in replay.GetTextures()}
    state["pixel_textures"] = []
    for index, binding in enumerate(used):
        texture = textures[binding.descriptor.resource]
        state["pixel_textures"].append({
            "binding_order": index,
            "descriptor_index": binding.access.arrayElement,
            "resource": str(texture.resourceId),
            "width": texture.width,
            "height": texture.height,
            "format": texture.format.Name(),
            "mips": texture.mips,
            "samples": texture.msSamp,
        })
    foliage = [binding.descriptor.resource for binding in used
               if textures[binding.descriptor.resource].format.Name() == "BC3_UNORM"]
    assert len(foliage) == 1, "no unique BC3 pixel texture"
    subresource = rd.Subresource()
    subresource.mip = subresource.slice = subresource.sample = 0
    foliage_bytes = bytes(replay.GetTextureData(foliage[0], subresource))
    foliage_pixels = textures[foliage[0]].width * textures[foliage[0]].height
    assert len(foliage_bytes) == foliage_pixels, "unexpected BC3 mip-0 byte count"
    alpha_counts = [0] * 256
    for offset in range(0, len(foliage_bytes), 16):
        first, second = foliage_bytes[offset:offset + 2]
        if first > second:
            palette = [first, second] + [((7 - i) * first + i * second) // 7
                                         for i in range(1, 7)]
        else:
            palette = [first, second] + [((5 - i) * first + i * second) // 5
                                         for i in range(1, 5)] + [0, 255]
        selectors = int.from_bytes(foliage_bytes[offset + 2:offset + 8], "little")
        for pixel in range(16):
            alpha_counts[palette[(selectors >> (3 * pixel)) & 7]] += 1
    assert sum(alpha_counts) == foliage_pixels
    state["bc3_mip0"] = {
        "resource": str(foliage[0]),
        "bytes": len(foliage_bytes),
        "sha256": hashlib.sha256(foliage_bytes).hexdigest(),
        "alpha_zero": alpha_counts[0],
        "alpha_full": alpha_counts[255],
        "alpha_partial": sum(alpha_counts[1:255]),
        "prior_uses": [{"event": usage.eventId, "usage": str(usage.usage)}
                       for usage in replay.GetUsage(foliage[0])
                       if usage.eventId < event][-8:],
    }
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
    replay.SetFrameEvent(max(writes), True)
    source_bytes = bytes(replay.GetBufferData(source, 0, 0))
    replay.SetFrameEvent(copy_event, True)
    copied_bytes = bytes(replay.GetTextureData(target, subresource))
    replay.SetFrameEvent(event, True)
    sampled_bytes = bytes(replay.GetTextureData(target, subresource))
    assert source_bytes.startswith(copied_bytes) and sampled_bytes == copied_bytes
    fourth_channel = copied_bytes[3::4]
    assert len(fourth_channel) == textures[target].width * textures[target].height
    state["full_view_payload"] = {
        "source_offset": 0,
        "bytes": len(copied_bytes),
        "sha256": hashlib.sha256(copied_bytes).hexdigest(),
        "unchanged_at_draw": True,
        "byte3_zero": fourth_channel.count(0),
        "byte3_full": fourth_channel.count(255),
        "byte3_partial": len(fourth_channel) - fourth_channel.count(0)
                         - fourth_channel.count(255),
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
