#!/usr/bin/env python3
"""Verify the live FH1 player/car and view-8 car-presentation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PLAYER_PREFIX = "FH1 SNR01 Forza player "
PRESENTATION_PREFIX = "FH1 SNR01 car presentation "
LOCAL_PRESENTATION_PREFIX = "FH1 SNR01 local car presentation link "
DISCOVERY_PREFIX = "FH1 SNR01 local car presentation shared pointer "
SCENE_PACKET_PREFIX = "FH1 SNR01 scene indirect packet "


def records(path: Path, prefix: str) -> list[dict]:
    result = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = line.find(prefix)
        if marker >= 0:
            result.append(json.loads(line[marker + len(prefix) :]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--frame", type=int, default=6000)
    parser.add_argument("--require-local-presentation", action="store_true")
    parser.add_argument("--require-local-model", action="store_true")
    args = parser.parse_args()

    players = [r for r in records(args.log, PLAYER_PREFIX) if r["frame"] == args.frame]
    presentations = [
        r for r in records(args.log, PRESENTATION_PREFIX)
        if r["frame"] == args.frame
    ]
    assert len(players) == 8
    assert len({r["player"] for r in players}) == 8
    assert {r["vtable"] for r in players} == {0x8201EB4C}
    assert {r["link160_first_word"] for r in players} == {0x8200C29C}
    local_players = [r for r in players if r["link164"]]
    assert len(local_players) == 1
    assert local_players[0]["link164_first_word"] == 0x82014510

    assert len(presentations) == 8
    assert len({r["presentation"] for r in presentations}) == 8
    assert {r["constructor_arg"] for r in presentations} == {
        presentations[0]["constructor_arg"]
    }
    assert {r["constructor_arg_first_word"] for r in presentations} == {
        0x82001BF4
    }
    assert all(r["view8_owner"] for r in presentations)

    local_presentations = [
        r for r in records(args.log, LOCAL_PRESENTATION_PREFIX)
        if r["frame"] == args.frame
    ]
    if not local_presentations:
        local_presentations = [
            {
                "frame": r["frame"],
                "car": r["car"],
                "presentation": r["presentation"],
                "livery": r["shared"],
                "livery_vtable": r["shared_vtable"],
                "view8_owner": True,
            }
            for r in records(args.log, DISCOVERY_PREFIX)
            if r["frame"] == args.frame
            and r["car_offset"] == 12292
            and r["presentation_offset"] == 2800
        ]
    scene_packets = records(args.log, SCENE_PACKET_PREFIX)
    require_local = args.require_local_presentation or args.require_local_model
    if require_local:
        assert len(local_presentations) == 1
        local = local_presentations[0]
        assert local["car"] == local_players[0]["link160"]
        assert local["livery_vtable"] == 0x8222F4A4
        assert local["view8_owner"]
        assert local["presentation"] in {r["presentation"] for r in presentations}
        local_packets = [
            r for r in scene_packets
            if r["frame"] == args.frame
            and r["view_call"] == 8
            and r["flush_owner"] == local["presentation"]
        ]
        assert len(local_packets) == 12
        assert {r["flush_caller_lr"] for r in local_packets} == {0x8243CE0C}
        assert {r["flush_owner_first_word"] for r in local_packets} == {0x82003A54}
        assert len({r["target_physical"] for r in local_packets}) == 12
    model_packets = []
    if args.require_local_model:
        assert local["model_vtable"] == 0x82001618
        model_packets = [
            r for r in scene_packets
            if r["frame"] == args.frame
            and r["view_call"] == 8
            and r["flush_owner"] == local["model"]
        ]
        assert len(model_packets) == 37
        assert sum(r["flush_caller_lr"] == 0x824399F0 for r in model_packets) == 29
        assert sum(r["flush_caller_lr"] == 0x8241A2A4 for r in model_packets) == 8
        assert {r["flush_owner_first_word"] for r in model_packets} == {0x82001618}
        assert len({r["target_physical"] for r in model_packets}) == 37

    text = args.log.read_text(encoding="utf-8", errors="replace")
    direct_links = text.count("FH1 SNR01 local car owner link ")
    reverse_links = text.count("FH1 SNR01 local presentation car link ")
    assert direct_links == reverse_links == 0

    print(json.dumps({
        "frame": args.frame,
        "players": len(players),
        "local_players": len(local_players),
        "presentations": len(presentations),
        "view8_presentations": sum(r["view8_owner"] for r in presentations),
        "local_presentations": len(local_presentations),
        "local_view8_scene_packets": len(local_packets) if require_local else 0,
        "local_model_view8_scene_packets": len(model_packets),
        "direct_links": direct_links,
        "reverse_links": reverse_links,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
