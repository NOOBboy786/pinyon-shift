#!/usr/bin/env python3
"""Verify the live FH1 player/car and view-8 car-presentation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PLAYER_PREFIX = "FH1 SNR01 Forza player "
PRESENTATION_PREFIX = "FH1 SNR01 car presentation "


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
        "direct_links": direct_links,
        "reverse_links": reverse_links,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
