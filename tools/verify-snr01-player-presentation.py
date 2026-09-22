#!/usr/bin/env python3
"""Verify the live FH1 player/car and view-8 car-presentation evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


PLAYER_PREFIX = "FH1 SNR01 Forza player "
PRESENTATION_PREFIX = "FH1 SNR01 car presentation "
LOCAL_PRESENTATION_PREFIX = "FH1 SNR01 local car presentation link "
DISCOVERY_PREFIX = "FH1 SNR01 local car presentation shared pointer "
SCENE_PACKET_PREFIX = "FH1 SNR01 scene indirect packet "
CAR_OWNER_CALL_PREFIX = "FH1 SNR01 car owner call "
CAR_OWNER_SELECTION_PREFIX = "FH1 SNR01 car owner selection "


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
    parser.add_argument("--require-owner-calls", action="store_true")
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
    require_local = (
        args.require_local_presentation
        or args.require_local_model
        or args.require_owner_calls
    )
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
    if args.require_local_model or args.require_owner_calls:
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

    owner_call_summary = {}
    if args.require_owner_calls:
        owner_calls = [
            r for r in records(args.log, CAR_OWNER_CALL_PREFIX)
            if r["frame"] == args.frame
            and r["view_call"] == 8
            and r["owner"] in {local["presentation"], local["model"]}
        ]
        calls_by_id = {r["call"]: r for r in owner_calls}
        owner_packets = local_packets + model_packets
        assert all(r["owner_call"] in calls_by_id for r in owner_packets)
        assert all(
            r["flush_owner"] == calls_by_id[r["owner_call"]]["owner"]
            and r["owner_caller_lr"]
            == calls_by_id[r["owner_call"]]["caller_lr"]
            and r["owner_args"] == calls_by_id[r["owner_call"]]["owner_args"]
            for r in owner_packets
        )

        packet_counts = Counter(r["owner_call"] for r in owner_packets)
        presentation_calls = [
            r for r in owner_calls if r["owner"] == local["presentation"]
        ]
        model_calls = [r for r in owner_calls if r["owner"] == local["model"]]
        assert len(presentation_calls) == 20
        assert len(model_calls) == 31
        assert all(r["caller_lr"] for r in owner_calls)
        assert sum(r["call"] in packet_counts for r in presentation_calls) == 12
        assert sum(r["call"] not in packet_counts for r in presentation_calls) == 8
        assert all(packet_counts[r["call"]] == 1 for r in presentation_calls
                   if r["call"] in packet_counts)
        assert all(r["call"] in packet_counts for r in model_calls)
        assert Counter(packet_counts[r["call"]] for r in model_calls) == {
            1: 29,
            4: 2,
        }
        selections = [
            r for r in records(args.log, CAR_OWNER_SELECTION_PREFIX)
            if r["frame"] == args.frame
            and r["view_call"] == 8
            and r["owner"] == local["presentation"]
        ]
        assert len(selections) == len(presentation_calls)
        selection_by_call = {r["call"]: r["selected_list"] for r in selections}
        assert len(selection_by_call) == len(selections)
        assert all(selection_by_call[r["call"]] for r in presentation_calls
                   if r["call"] in packet_counts)
        assert all(not selection_by_call[r["call"]] for r in presentation_calls
                   if r["call"] not in packet_counts)
        assert all(
            selection_by_call[r["owner_call"]] == r["list_object"]
            for r in local_packets
        )
        presentation_callers = Counter(r["caller_lr"] for r in presentation_calls)
        model_callers = Counter(r["caller_lr"] for r in model_calls)
        assert presentation_callers == {
            0x82437A04: 1,
            0x82437A3C: 1,
            0x82437CFC: 2,
            0x82437EA8: 1,
            0x824383CC: 1,
            0x8243842C: 1,
            0x824384EC: 1,
            0x8243D270: 12,
        }
        assert model_callers == {
            0x8243786C: 17,
            0x82437900: 10,
            0x824380AC: 1,
            0x824385C0: 1,
            0x8245AB44: 2,
        }
        owner_call_summary = {
            "local_presentation_owner_calls": len(presentation_calls),
            "local_presentation_no_submission_calls": 8,
            "local_presentation_null_selection_calls": 8,
            "local_model_owner_calls": len(model_calls),
            "local_model_no_submission_calls": 0,
            "local_presentation_callers": {
                hex(k): v for k, v in sorted(presentation_callers.items())
            },
            "local_model_callers": {
                hex(k): v for k, v in sorted(model_callers.items())
            },
        }

    text = args.log.read_text(encoding="utf-8", errors="replace")
    direct_links = text.count("FH1 SNR01 local car owner link ")
    reverse_links = text.count("FH1 SNR01 local presentation car link ")
    assert direct_links == reverse_links == 0

    summary = {
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
    }
    summary.update(owner_call_summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
