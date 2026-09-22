"""Check frame-wide draw accounting across two title source frames."""

import runpy
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "summarize-snr01-frame-wide-census.py")
)
SUMMARIZE = SCRIPT["summarize"]
READ_RECORDS = SCRIPT["read_records"]


class FrameWideCensusTest(unittest.TestCase):
    def test_direct_packet_inherits_only_its_thread_view_scope(self):
        events = (
            ("view begin", {"frame": 10, "call": 8, "view": 123}),
            ("direct packet", {"frame": 10, "header_physical": 4}),
            ("view end", {"frame": 10, "call": 8, "view": 123}),
            ("direct packet", {"frame": 10, "header_physical": 8}),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.log"
            path.write_text("".join(
                f"[t7] FH1 SNR01 {kind} {json.dumps(row)}\n"
                for kind, row in events), encoding="utf-8")
            rows = READ_RECORDS(path, {10, 11}, 11)["direct"]
        self.assertEqual([row["title_view_call"] for row in rows], [8, 0])

    def test_scene_owner_direct_root_and_unmatched_child(self):
        records = {key: [] for key in
                   ("primary", "scene", "execution", "draw", "view_begin",
                    "view_end", "direct", "semantic")}
        for frame in (10, 11):
            for call in range(1, 9):
                row = {"frame": frame, "call": call, "view": frame * 100 + call}
                records["view_begin"].append(row)
                records["view_end"].append(row)
        records["primary"] = [
            {"frame": 10, "header_physical": 100, "gpu_target": 1000},
            {"frame": 11, "header_physical": 200, "gpu_target": 2000},
        ]
        records["scene"] = [
            {"frame": 10, "header_physical": 300, "target_physical": 3000,
             "view_call": 8, "view": 1008, "flush_owner": 400,
             "flush_owner_first_word": 500, "flush_caller_lr": 600},
        ]
        records["execution"] = [
            {"execution": 1, "parent": 0, "dispatch_packet_physical": 100,
             "command_buffer": 1000},
            {"execution": 2, "parent": 1, "dispatch_packet_physical": 300,
             "command_buffer": 3000},
            {"execution": 3, "parent": 0, "dispatch_packet_physical": 200,
             "command_buffer": 2000},
            {"execution": 4, "parent": 3, "dispatch_packet_physical": 400,
             "command_buffer": 4000},
        ]
        records["draw"] = [
            {"ordinal": ordinal, "indirect_execution": execution,
             "surface_info": 1, "color_info": [2], "depth_info": 3,
             "render_target_bits": 3, "packet_physical": ordinal * 4}
            for ordinal, execution in enumerate((2, 1, 4, 3), 1)
        ]
        result = SUMMARIZE(records, [10, 11], 11)
        self.assertEqual(result["totals"]["draws"], 4)
        self.assertEqual(result["totals"]["classifications"],
                         {"view_owner": 1, "direct_root": 2,
                          "unmatched_indirect": 1})
        self.assertEqual(result["totals"]["draws_by_scene_source_frame"], {10: 1})
        self.assertEqual(len(result["draws"]), 4)


if __name__ == "__main__":
    unittest.main()
