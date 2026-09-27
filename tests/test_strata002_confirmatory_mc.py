from __future__ import annotations

import copy
import unittest

from finite_ram_lab.strata002_confirmatory_mc import _candidate, analyze


BASE = {
    "analysis_id": "STRATA-002-CONFIRMATORY-MC-v1",
    "source_run": 1,
    "source_artifact_id": 2,
    "source_artifact_digest": "sha256:test",
    "pilot_blocks": 8,
    "pilot_efficacy_successes": 8,
    "efficacy_alpha_one_sided": 0.025,
    "design_success_probability": 0.8,
    "conservative_success_probability": 0.6876560219336321,
    "latency_ratio_target": 1.25,
    "latency_one_sided_confidence": 0.95,
    "pilot_scan_ratio_values": [
        1.0443856304534282,
        1.0095148167898071,
        0.2599925020804434,
        2.9691211394039363,
        0.5597804522824279,
        1.4650049269252898,
        0.7690888216175071,
        2.0247057409224176,
    ],
    "candidate_blocks": [16, 24],
    "monte_carlo_resamples_per_candidate": 2000,
    "seed": 2026092803,
    "authority": "DESIGN_ONLY_NO_PHYSICAL_LAUNCH",
}


class Strata002ConfirmatoryMcTests(unittest.TestCase):
    def test_analysis_is_deterministic(self) -> None:
        a = analyze(copy.deepcopy(BASE))
        b = analyze(copy.deepcopy(BASE))
        self.assertEqual(a, b)

    def test_frozen_cp_lower_bound_is_verified(self) -> None:
        bad = copy.deepcopy(BASE)
        bad["conservative_success_probability"] = 0.9
        with self.assertRaises(ValueError):
            analyze(bad)

    def test_candidate_rates_are_probabilities(self) -> None:
        row = _candidate(
            n_blocks=16,
            reps=1000,
            seed=7,
            efficacy_p=0.70,
            efficacy_alpha=0.025,
            latency_log_mean=0.0,
            latency_log_sd=0.2,
            latency_ratio_target=1.25,
            latency_confidence=0.95,
            chunk_size=250,
        )
        for key in (
            "efficacy_design_assurance",
            "latency_design_assurance",
            "joint_design_assurance",
        ):
            self.assertGreaterEqual(row[key], 0.0)
            self.assertLessEqual(row[key], 1.0)

    def test_joint_never_exceeds_marginals(self) -> None:
        result = analyze(copy.deepcopy(BASE))
        for row in result["candidates"]:
            self.assertLessEqual(
                row["joint_design_assurance"],
                row["efficacy_design_assurance"],
            )
            self.assertLessEqual(
                row["joint_design_assurance"],
                row["latency_design_assurance"],
            )


if __name__ == "__main__":
    unittest.main()
