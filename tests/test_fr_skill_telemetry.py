from __future__ import annotations

import unittest

from finite_ram_lab.fr_skill_telemetry import (
    aggregate,
    assess_event,
    fr_meta_015_event,
    run_panel,
)


class SkillTelemetryTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(
            result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                result["checks"].values()
            )
        )

    def test_first_event_is_skill_hit(self) -> None:
        row = assess_event(
            fr_meta_015_event()
        )
        self.assertTrue(
            row["skill_hit"]
        )
        self.assertTrue(
            row["qualified"]
        )
        self.assertGreater(
            row[
                "context_reduction_fraction"
            ],
            0.97,
        )

    def test_unobserved_reversal_is_not_zero(self) -> None:
        summary = aggregate(
            [
                fr_meta_015_event()
            ]
        )
        self.assertIsNone(
            summary[
                "reversal"
            ]["rate"]
        )
        self.assertEqual(
            summary[
                "reversal"
            ]["observed"],
            0,
        )
        self.assertEqual(
            summary[
                "reversal"
            ]["coverage"],
            0.0,
        )

    def test_one_event_cannot_support_general_effect_claim(self) -> None:
        summary = aggregate(
            [
                fr_meta_015_event()
            ]
        )
        self.assertFalse(
            summary[
                "effect_claim_ready"
            ]
        )

    def test_authority_expansion_is_critical(self) -> None:
        event = fr_meta_015_event()
        event[
            "authority_expanded"
        ] = True

        row = assess_event(
            event
        )
        self.assertEqual(
            row["risk"],
            "CRITICAL",
        )
        self.assertFalse(
            row["qualified"]
        )


if __name__ == "__main__":
    unittest.main()
