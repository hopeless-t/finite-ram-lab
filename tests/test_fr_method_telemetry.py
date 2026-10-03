from __future__ import annotations

import unittest

from finite_ram_lab.fr_method_telemetry import (
    aggregate,
    assess_event,
    monte_carlo_call_budget_sensitivity,
    run_panel,
    synthetic_fixtures,
)


class MethodTelemetryTests(unittest.TestCase):
    def test_panel_passes(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["invariants"].values()))

    def test_unknown_is_not_imputed_to_zero(self) -> None:
        summary = aggregate(
            [
                {
                    "event_id": "UNKNOWN",
                    "bounce_id": "B-UNKNOWN",
                    "protocol": "MIXED_V3",
                    "gap_class": "MODEL_GAP",
                    "external_tool_calls": None,
                    "authority_expanded": False,
                }
            ]
        )
        calls = summary["means"]["external_tool_calls"]
        self.assertIsNone(calls["value"])
        self.assertEqual(calls["observed"], 0)
        self.assertEqual(calls["coverage"], 0.0)

    def test_stall_fixture_is_review(self) -> None:
        stall = next(
            row for row in synthetic_fixtures()
            if row["event_id"] == "STALL-001"
        )
        assessment = assess_event(stall)
        self.assertEqual(assessment["risk"], "REVIEW")
        self.assertIn(
            "EXTERNAL_CALL_BUDGET_EXCEEDED",
            assessment["violations"],
        )
        self.assertIn(
            "NON_ATOMIC_DURABLE_TRANSITION",
            assessment["violations"],
        )

    def test_synthetic_mc_does_not_mutate_policy(self) -> None:
        result = monte_carlo_call_budget_sensitivity(trials=5000)
        self.assertEqual(result["current_policy_threshold"], 6)
        self.assertEqual(
            result["decision"],
            "NO_THRESHOLD_CHANGE_FROM_SYNTHETIC_ONLY",
        )
        self.assertEqual(
            [row["threshold"] for row in result["rows"]],
            [4, 5, 6, 7, 8],
        )


if __name__ == "__main__":
    unittest.main()
