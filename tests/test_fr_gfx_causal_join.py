from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_causal_join import (
    _synthetic_fixture,
    causal_asof,
    run_panel,
)


class FrGfxCausalJoinTests(
    unittest.TestCase
):
    def test_future_sample_is_not_used(self):
        rows = [
            {
                "timestamp_monotonic_ns": (
                    110
                ),
                "value": "future",
            },
        ]

        result = causal_asof(
            timestamp_ns=100,
            rows=rows,
            timestamps=[110],
            max_age_ns=1000,
        )

        self.assertTrue(
            result["missing"]
        )
        self.assertIsNone(
            result["value"]
        )

    def test_stale_is_explicit(self):
        rows = [
            {
                "timestamp_monotonic_ns": (
                    10
                ),
                "value": 1,
            },
        ]

        result = causal_asof(
            timestamp_ns=100,
            rows=rows,
            timestamps=[10],
            max_age_ns=50,
        )

        self.assertTrue(
            result["stale"]
        )
        self.assertFalse(
            result["missing"]
        )
        self.assertIsNone(
            result["value"]
        )

    def test_fixture_rejects_future_frame(self):
        fixture = (
            _synthetic_fixture()
        )

        row = fixture[
            "joined"
        ][2][
            "joined_evidence"
        ]["frame"]

        self.assertTrue(
            row["stale"]
        )
        self.assertEqual(
            row[
                "source_timestamp_ns"
            ],
            1900,
        )

    def test_panel_has_zero_future_leakage(self):
        result = run_panel()

        self.assertEqual(
            result[
                "invariants"
            ][
                "future_leakage_count"
            ],
            0,
        )

    def test_claim_ceiling(self):
        result = run_panel()

        self.assertEqual(
            result[
                "claim_ceiling"
            ],
            "CAUSAL_OFFLINE_JOIN_CONTRACT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
