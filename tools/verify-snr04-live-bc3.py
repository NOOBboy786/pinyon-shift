"""Verify the selected same-frame packet, SRV, and BC3 readback join."""

import collections
import hashlib
import json
from pathlib import Path
import re
import sys


def verify(log_path: Path, output_dir: Path) -> dict:
    scenes = {}
    bindings = collections.defaultdict(set)
    readbacks = {}
    frames = set()
    readback_frames = set()
    submissions = set()
    for line in log_path.read_text(encoding="utf-8-sig").splitlines():
        if "FH1 scene binding " in line:
            row = json.loads(line.split("FH1 scene binding ", 1)[1])
            packet = row["packet_physical"]
            fetch_zero = next((part[2:] for part in row["textures"].split(";")
                               if part.startswith("0:")), None)
            if fetch_zero and row["vertex_shader"] == "5834939992FFC765" and \
                    row["pixel_shader"] == "C2F1242C2535A57E":
                assert packet not in scenes or scenes[packet] == fetch_zero
                scenes[packet] = fetch_zero
        elif "FH1 SNR04 bound pixel " in line:
            row = json.loads(line.split("FH1 SNR04 bound pixel ", 1)[1])
            if row["fetch"] == 0 and not row["signed"]:
                frames.add(row["frame"])
                bindings[row["packet"]].add(row["absolute"])
        elif "FH1 SNR04 BC3 readback " in line:
            match = re.search(r"frame=(\d+) submission=(\d+) srv=(\d+) "
                              r"written=(\w+) path=(.*)$", line)
            assert match, line
            frame, submission, srv, written, path = match.groups()
            assert written == "true"
            readback_frames.add(int(frame))
            submissions.add(int(submission))
            assert Path(path).resolve().parent == output_dir.resolve()
            assert int(srv) not in readbacks
            data = Path(path).read_bytes()
            assert len(data) == 65536
            readbacks[int(srv)] = hashlib.sha256(data).hexdigest()
        elif "FH1 SNR04 BC3 " in line:
            raise AssertionError(line)

    assert len(frames) == 1 and readback_frames == frames and \
        len(submissions) == 1 and scenes and set(bindings) == set(scenes)
    packet_srvs = {packet: next(iter(srvs)) for packet, srvs in bindings.items()
                   if len(srvs) == 1}
    assert len(packet_srvs) == len(scenes)
    descriptor_srvs = collections.defaultdict(set)
    for packet, descriptor in scenes.items():
        descriptor_srvs[descriptor].add(packet_srvs[packet])
    assert len(descriptor_srvs) == 5
    assert all(len(srvs) == 1 for srvs in descriptor_srvs.values())
    assert set(packet_srvs.values()) == set(readbacks)
    return {"frame": frames.pop(), "packets": len(scenes),
            "srvs": {str(srv): sha for srv, sha in sorted(readbacks.items())}}


if __name__ == "__main__":
    assert len(sys.argv) == 3, "usage: verify-snr04-live-bc3.py LOG OUTPUT_DIR"
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
