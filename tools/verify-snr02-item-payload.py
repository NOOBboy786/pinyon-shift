"""Join selected procedural draw packets to bounded title record payloads."""

import collections
import json
from pathlib import Path
import re
import sys


CANDIDATE = {
    "14020500/00030000/00010400/00000003",
    "14020500/000C0000/00010400/00000003",
}


def verify(log: Path, ledger: Path) -> dict:
    items, payloads = {}, {}
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        for marker, destination in (("FH1 SNR01 procedural item ", items),
                                    ("FH1 SNR02 item payload ", payloads)):
            if marker not in line:
                continue
            row = json.loads(line.split(marker, 1)[1])
            key = row["frame"], row["call"]
            assert key not in destination, key
            destination[key] = row
    assert payloads and set(payloads) <= set(items)
    for key, payload in payloads.items():
        item = items[key]
        assert item["descriptor_seen"] and item["runtime_seen"]
        assert (payload["descriptor"], payload["runtime"], payload["kind"]) == (
            item["descriptor_address"], item["runtime_address"],
            item["descriptor_kind"])
        assert re.fullmatch(r"[0-9A-F]{184}", payload["descriptor_words"])
        assert re.fullmatch(r"[0-9A-F]{136}", payload["runtime_words"])
        assert int(payload["descriptor_words"][72:80], 16) == payload["kind"]
    draws = [row for row in json.loads(ledger.read_text())["draws"]
             if row["target"] in CANDIDATE and
             row["title_packet_caller_lr"] == 0x82415D1C]
    selected = {(row["title_packet_source_frame"], row["title_item_call"])
                for row in draws}
    assert draws and selected <= set(payloads)
    assert all(items[key]["submit_seen"] for key in selected)
    by_runtime = collections.defaultdict(list)
    for payload in payloads.values():
        by_runtime[payload["runtime"]].append(payload)
    changed_words = collections.Counter()
    changed_pointers = 0
    for samples in by_runtime.values():
        values = [sample["runtime_words"] for sample in samples]
        if len(set(values)) <= 1:
            continue
        changed_pointers += 1
        for word in range(17):
            if len({value[word * 8:word * 8 + 8] for value in values}) > 1:
                changed_words[word] += 1
    return {"selected_draws": len(draws), "selected_calls": len(selected),
            "payloads": len(payloads), "kinds": dict(sorted(collections.Counter(
                payloads[key]["kind"] for key in selected).items())),
            "reused_runtime_pointers_with_changes": changed_pointers,
            "changed_runtime_words": dict(sorted(changed_words.items()))}


if __name__ == "__main__":
    assert len(sys.argv) == 3, "usage: verify-snr02-item-payload.py LOG LEDGER"
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
