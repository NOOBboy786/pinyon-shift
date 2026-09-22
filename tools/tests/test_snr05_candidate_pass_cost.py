"""Check candidate pass timing joins without treating unknowns as savings."""

import json
import runpy
import unittest
from pathlib import Path


SUMMARIZE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                               "summarize-snr05-candidate-pass-cost.py"))["summarize"]


class CandidatePassCostTest(unittest.TestCase):
    def test_attachment_join_and_unknown_cost(self):
        target = "14020500/00030000/00010400/00000003"
        draw = {"frame": 11, "surface_info": 0x14020500,
                "color_info": [0x30000], "depth_info": 0x10400,
                "render_target_bits": 3, "attachment_state": 0xA}
        sample = {"frame": 10, "family": "0000000000000001",
                  "total_ns": 2_000_000, "prepare_cpu_ns": 400_000}
        unknown = {**sample, "family": "0000000000000002",
                   "total_ns": 100_000, "prepare_cpu_ns": 0}
        lines = [
            "FH1 SNR01 prepared draw " + json.dumps(draw),
            "FH1 V5 pass family 0000000000000001: attachment 000000000000000A",
            "FH1 V5 pass sample " + json.dumps(sample),
            "FH1 V5 pass sample " + json.dumps(unknown),
            'FH1 timing loss reasons {"busy":0,"capacity":0,"interrupted":0,"invalid":0}',
        ]
        result = SUMMARIZE(lines, 11, 10, 10, {target})
        self.assertEqual(result["medians_ms"]["candidate_gpu_ms"], 2)
        self.assertEqual(result["frames"][0]["unmapped_gpu_ms"], 0.1)
        self.assertEqual(result["frames"][0]["candidate_prepare_cpu_ms"], 0.4)
        self.assertFalse(result["limits"]["removable_cost_proved"])
        with self.assertRaisesRegex(ValueError, "losses"):
            SUMMARIZE(lines[:-1] + ['FH1 timing loss reasons {"busy":1}'],
                      11, 10, 10, {target})


if __name__ == "__main__":
    unittest.main()
