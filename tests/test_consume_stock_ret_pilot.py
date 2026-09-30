from __future__ import annotations

import unittest

from finite_ram_lab.consume_stock_ret_pilot import classify_capability


class ConsumeStockRetPilotTests(unittest.TestCase):
    def test_capture_requires_clean_observation(self) -> None:
        self.assertEqual(
            classify_capability(
                normalized=True,
                trace_complete=True,
                worker_ok=True,
                cpu_ok=True,
                pte_ok=True,
                probe_missed=0,
                target_receipt_count=1,
            ),
            "CONSUME_STOCK_RET_CAPTURED",
        )

    def test_zero_receipt_is_capability_not_observed(self) -> None:
        self.assertEqual(
            classify_capability(
                normalized=True,
                trace_complete=True,
                worker_ok=True,
                cpu_ok=True,
                pte_ok=True,
                probe_missed=0,
                target_receipt_count=0,
            ),
            "CAPABILITY_NOT_OBSERVED",
        )

    def test_probe_miss_is_instrumentation_hold(self) -> None:
        self.assertEqual(
            classify_capability(
                normalized=True,
                trace_complete=True,
                worker_ok=True,
                cpu_ok=True,
                pte_ok=True,
                probe_missed=1,
                target_receipt_count=1,
            ),
            "INSTRUMENTATION_HOLD",
        )

    def test_preverify_hold_precedes_receipt(self) -> None:
        self.assertEqual(
            classify_capability(
                normalized=False,
                trace_complete=True,
                worker_ok=True,
                cpu_ok=True,
                pte_ok=True,
                probe_missed=0,
                target_receipt_count=1,
            ),
            "PREVERIFY_HOLD",
        )


if __name__ == "__main__":
    unittest.main()
