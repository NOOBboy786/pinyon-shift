"""Run with qrenderdoc --python to verify the captured vegetation quad order.

Set SNR04_CAPTURE, SNR04_OUTPUT and SNR04_EVENT in the environment. The output
JSON reports validity because qrenderdoc does not propagate Python exit codes.
"""

import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import traceback

import renderdoc as rd


EXPECTED_VS = "2adfe080228c468ce9aec7e21d19798fc8aaa32cdba5d7325c4fac4070f21faa"
EXPECTED_TRIANGLES = (0, 1, 3, 1, 2, 3)


def inspect(capture, event):
    file = rd.OpenCaptureFile()
    replay = None
    try:
        opened = file.OpenFile(str(capture), "rdc", None)
        assert "Success" in str(opened), opened
        result, replay = file.OpenCapture(rd.ReplayOptions(), None)
        assert "Success" in str(result), result
        actions = {action.eventId: action for action in replay.GetRootActions()}
        assert event in actions and actions[event].flags & rd.ActionFlags.Drawcall
        assert actions[event].numIndices == 160
        replay.SetFrameEvent(event, True)
        pipeline = replay.GetPipelineState()
        shader = pipeline.GetShaderReflection(rd.ShaderStage.Vertex)
        vs_hash = hashlib.sha256(bytes(shader.rawBytes)).hexdigest()
        assert vs_hash == EXPECTED_VS, vs_hash
        assert pipeline.GetPrimitiveTopology() == rd.Topology.LineList_Adj
        depth_state = pipeline.GetDepthTestState()
        assert depth_state.depthEnable and depth_state.depthWrites
        assert depth_state.depthFunction == rd.CompareFunction.GreaterEqual

        positions = {}
        counts = {}
        for name, stage, count in (("vs", rd.MeshDataStage.VSOut, 160),
                                   ("gs", rd.MeshDataStage.GSOut, 240)):
            mesh = replay.GetPostVSData(0, 0, stage)
            assert mesh.numIndices == count and mesh.vertexByteStride >= 16
            raw = bytes(replay.GetBufferData(mesh.vertexResourceId,
                                             mesh.vertexByteOffset,
                                             mesh.vertexByteSize))
            assert len(raw) >= count * mesh.vertexByteStride
            positions[name] = [raw[i * mesh.vertexByteStride:
                                   i * mesh.vertexByteStride + 16]
                               for i in range(count)]
            counts[name] = count

        observed = []
        ambiguous = []
        for quad in range(40):
            vertices = positions["vs"][quad * 4:quad * 4 + 4]
            if len(set(vertices)) == 1:
                continue
            if len(set(vertices)) != 4:
                ambiguous.append(quad)
                continue
            triangle_vertices = positions["gs"][quad * 6:quad * 6 + 6]
            pattern = tuple(vertices.index(vertex) if vertex in vertices else -1
                            for vertex in triangle_vertices)
            observed.append((quad, pattern))
        assert not ambiguous, f"ambiguous quads: {ambiguous}"
        assert observed and all(pattern == EXPECTED_TRIANGLES
                                for _, pattern in observed), observed
        quad, _ = observed[0]
        coordinates = [struct.unpack("<4f", value)
                       for value in positions["vs"][quad * 4:quad * 4 + 4]]
        return dict(valid=True, event=event, vs_sha256=vs_hash,
                    topology=str(pipeline.GetPrimitiveTopology()),
                    depth_test=str(depth_state.depthFunction),
                    vs_vertices=counts["vs"], gs_vertices=counts["gs"],
                    degenerate_quads=40 - len(observed),
                    nondegenerate_quads=[quad for quad, _ in observed],
                    triangle_indices=list(EXPECTED_TRIANGLES),
                    first_nondegenerate_positions=coordinates)
    finally:
        if replay is not None:
            replay.Shutdown()
        file.Shutdown()


def main():
    output = Path(os.environ["SNR04_OUTPUT"])
    try:
        result = inspect(Path(os.environ["SNR04_CAPTURE"]),
                         int(os.environ["SNR04_EVENT"]))
    except Exception:
        result = dict(valid=False, error=traceback.format_exc())
    output.write_text(json.dumps(result, indent=2))
    sys.exit(0)


main()
