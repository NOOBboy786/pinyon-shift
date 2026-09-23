"""Census pixel inputs of the matched vegetation draws in one RenderDoc frame.

Run with qrenderdoc --python and SNR04_CAPTURE, SNR04_EVENTS_JSON, SNR04_OUTPUT.
Set SNR04_BC3_DIR to save the same-frame compressed BC3 mip-0 bytes.
"""

import collections
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import traceback

import renderdoc as rd


events = [row["event"] for row in json.loads(Path(
    os.environ["SNR04_EVENTS_JSON"]).read_text())["matches"]]
output = Path(os.environ["SNR04_OUTPUT"])
bc3_dir = Path(os.environ["SNR04_BC3_DIR"]) if os.environ.get("SNR04_BC3_DIR") else None
state = {"stage": "open", "events": len(events), "draws": [],
         "skipped": [], "bc3_payloads": {}}
cap = replay = None
try:
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(os.environ["SNR04_CAPTURE"], "rdc", None)
    if "Success" not in str(result):
        raise RuntimeError(str(result))
    result, replay = cap.OpenCapture(rd.ReplayOptions(), None)
    if "Success" not in str(result):
        raise RuntimeError(str(result))
    textures = {texture.resourceId: texture for texture in replay.GetTextures()}
    shaders = {}
    for event in events:
        replay.SetFrameEvent(event, True)
        pipeline = replay.GetPipelineState()
        used = pipeline.GetReadOnlyResources(rd.ShaderStage.Pixel)
        if len(used) != 2:
            state["skipped"].append({"event": event, "pixel_textures": len(used)})
            continue
        resources = [textures[binding.descriptor.resource] for binding in used]
        if [resource.format.Name() for resource in resources] != [
                "BC3_UNORM", "R8G8B8A8_TYPELESS"]:
            state["skipped"].append({"event": event,
                                     "pixel_formats": [resource.format.Name()
                                                       for resource in resources]})
            continue
        cb = pipeline.GetConstantBlock(rd.ShaderStage.Pixel, 3, 0).descriptor
        words = struct.unpack("<8I", bytes(replay.GetBufferData(
            cb.resource, cb.byteOffset, 32)))
        assert [binding.access.arrayElement for binding in used] == [
            words[2], words[5]], (event, "descriptor indices")
        shader = pipeline.GetShaderReflection(rd.ShaderStage.Pixel)
        shader_hash = hashlib.sha256(bytes(shader.rawBytes)).hexdigest()
        if shader_hash not in shaders:
            assembly = replay.DisassembleShader(
                pipeline.GetGraphicsPipelineObject(), shader, "")
            shaders[shader_hash] = {
                "resource": str(pipeline.GetShader(rd.ShaderStage.Pixel)),
                "alpha_product": "mul r7.w, r3.w, r4.w" in assembly,
                "discard_count": assembly.count("discard_z"),
                "sample_four_channels": bool(re.search(r"sample_d .*\.xyzw,", assembly)),
                "sample_first_channel": bool(re.search(r"sample_d .*\.x,", assembly)),
            }
        bc3 = str(resources[0].resourceId)
        if bc3 not in state["bc3_payloads"]:
            subresource = rd.Subresource()
            subresource.mip = subresource.slice = subresource.sample = 0
            payload = bytes(replay.GetTextureData(resources[0].resourceId, subresource))
            assert len(payload) == resources[0].width * resources[0].height
            if bc3_dir:
                bc3_dir.mkdir(parents=True, exist_ok=True)
                (bc3_dir / (bc3.replace("::", "-") + ".bc3")).write_bytes(payload)
            state["bc3_payloads"][bc3] = {
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "prior_uses": [usage.eventId for usage in replay.GetUsage(
                    resources[0].resourceId) if usage.eventId < event],
            }
        state["draws"].append({
            "event": event,
            "shader_sha256": shader_hash,
            "bc3": bc3,
            "full_view": str(resources[1].resourceId),
            "descriptor_indices": [words[2], words[5]],
        })
        if (len(state["draws"]) + len(state["skipped"])) % 20 == 0:
            output.write_text(json.dumps(state, sort_keys=True))
    state["pixel_shaders"] = shaders
    state["bc3_draw_counts"] = dict(collections.Counter(
        row["bc3"] for row in state["draws"]))
    state["full_view_draw_counts"] = dict(collections.Counter(
        row["full_view"] for row in state["draws"]))
    assert state["draws"] and all(
        row.get("pixel_textures") == 0 for row in state["skipped"]), \
        "unexpected matched draw path"
    assert len(shaders) == 1 and len(state["full_view_draw_counts"]) == 1
    assert all(shader["alpha_product"] and shader["discard_count"] > 0 and
               shader["sample_four_channels"] and shader["sample_first_channel"]
               for shader in shaders.values()), "unexpected pixel shader path"
    state["stage"] = "done"
except Exception:
    state.update(stage="error", error=traceback.format_exc())
finally:
    output.write_text(json.dumps(state, sort_keys=True))
    if replay:
        replay.Shutdown()
    if cap:
        cap.Shutdown()
