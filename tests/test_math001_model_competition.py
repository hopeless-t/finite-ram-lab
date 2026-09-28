from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from finite_ram_lab.math001_model_competition import (
    analyze,
    load_evidence,
    residual_scores,
    trial_mdl,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/MEMCG-001/event-sequence-v1.json"


class Math001Tests(unittest.TestCase):
    def test_actual_evidence_selects_q64(self) -> None:
        result = analyze(load_evidence(EVIDENCE))
        self.assertEqual(result["decision"], "MODEL64_WINS")
        self.assertEqual(result["minimum_reset_sse_q"], 64)
        self.assertEqual(result["minimum_mdl_q"], 64)
        self.assertTrue(
            all(f["trained_q"] == 64 for f in result["leave_one_block_out"])
        )
        self.assertTrue(
            all(math.isclose(f["f1"], 1.0) for f in result["leave_one_block_out"])
        )

    def test_divisor_alias_is_penalized(self) -> None:
        data = load_evidence(EVIDENCE)
        trial = next(
            t for t in data["trials"]
            if t["block"] == 0 and t["mode"] == "touch"
        )
        q64 = trial_mdl(trial, 64)
        q32 = trial_mdl(trial, 32)
        q8 = trial_mdl(trial, 8)
        self.assertLess(q64["bits"], q32["bits"])
        self.assertLess(q64["bits"], q8["bits"])

    def test_reset_aware_q64_exactly_fits_block2(self) -> None:
        data = load_evidence(EVIDENCE)
        trial = next(
            t for t in data["trials"]
            if t["block"] == 2 and t["mode"] == "touch"
        )
        reset = residual_scores(trial, 64, reset_aware=True)
        stationary = residual_scores(trial, 64, reset_aware=False)
        self.assertEqual(reset["sse"], 0.0)
        self.assertGreater(stationary["sse"], 0.0)
        self.assertEqual(len(reset["segments"]), 2)

    def test_controls_have_no_positive_events(self) -> None:
        result = analyze(load_evidence(EVIDENCE))
        self.assertEqual(result["controls_positive_events"], 0)

    def test_uniform_null_sanity_value(self) -> None:
        result = analyze(load_evidence(EVIDENCE))
        self.assertAlmostEqual(
            result["clean_four_jump_uniform_null_probability"],
            64 / math.comb(256, 4),
        )


if __name__ == "__main__":
    unittest.main()
