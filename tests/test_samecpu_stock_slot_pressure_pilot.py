from __future__ import annotations

import unittest

from finite_ram_lab.samecpu_stock_slot_pressure_pilot import (
    _hist_dropped,
    classify_trial,
)


class SameCpuSlotPressurePilotTests(unittest.TestCase):
    def test_clean_eviction_fingerprint_matches(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=True,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=0,
                target_drain_count=1,
                drain_pages=[31],
                helpers_started=8,
                all_started_helpers_realized=True,
                diagnostic_q64_count=1,
            ),
            "EVICTION_FINGERPRINT_MATCH",
        )

    def test_refill_confounds_before_eviction_claim(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=True,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=1,
                target_drain_count=1,
                drain_pages=[31],
                helpers_started=5,
                all_started_helpers_realized=True,
                diagnostic_q64_count=1,
            ),
            "PRESSURE_CONFOUNDED_BY_OWNER_REFILL",
        )

    def test_bound_violation_requires_13_realized_helpers(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=True,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=0,
                target_drain_count=0,
                drain_pages=[],
                helpers_started=13,
                all_started_helpers_realized=True,
                diagnostic_q64_count=0,
            ),
            "SLOT_EVICTION_BOUND_VIOLATION_CANDIDATE",
        )

    def test_unrealized_helper_is_not_bound_violation(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=True,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=0,
                target_drain_count=0,
                drain_pages=[],
                helpers_started=13,
                all_started_helpers_realized=False,
                diagnostic_q64_count=0,
            ),
            "HELPER_INSERTION_NOT_REALIZED",
        )

    def test_drain_size_mismatch_is_separate(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=True,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=0,
                target_drain_count=1,
                drain_pages=[30],
                helpers_started=7,
                all_started_helpers_realized=True,
                diagnostic_q64_count=1,
            ),
            "TARGET_DRAIN_SIZE_MISMATCH",
        )

    def test_probe_miss_holds(self) -> None:
        self.assertEqual(
            classify_trial(
                precondition_ok=True,
                coverage_ok=False,
                hist_dropped=0,
                pressure_trace_complete=True,
                pressure_unknown_count=0,
                pressure_owner_refill_delta=0,
                target_drain_count=1,
                drain_pages=[31],
                helpers_started=7,
                all_started_helpers_realized=True,
                diagnostic_q64_count=1,
            ),
            "INSTRUMENTATION_HOLD",
        )

    def test_hist_dropped_parser(self) -> None:
        self.assertEqual(
            _hist_dropped("Totals:\n    Hits: 12\n    Dropped: 0\n"),
            0,
        )
        self.assertEqual(
            _hist_dropped("Totals:\n    Hits: 12\n    Dropped: 3\n"),
            3,
        )
        self.assertIsNone(_hist_dropped("no totals"))


if __name__ == "__main__":
    unittest.main()
