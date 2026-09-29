from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finite_ram_lab.transactional_spawn_native import (
    marker_text,
    observed_window,
    receipt_after_touch,
    touch_with_transaction_marker,
)


class TransactionalSpawnNativeTests(unittest.TestCase):
    def test_marker_text_is_epoch_scoped(self) -> None:
        self.assertEqual(
            marker_text(
                trial_id="3:7",
                epoch=2,
                phase="CONSUME",
                touch_number=11,
                edge="PRE",
            ),
            "FRL_TX trial=3:7 epoch=2 phase=CONSUME touch=11 PRE",
        )

    def test_touch_wrapper_always_writes_post_marker(self) -> None:
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / "trace_marker"

            def fake_write(path: Path, **kwargs) -> None:
                calls.append(kwargs["edge"])

            with (
                patch(
                    "finite_ram_lab.transactional_spawn_native.write_marker",
                    side_effect=fake_write,
                ),
                patch(
                    "finite_ram_lab.transactional_spawn_native._touch",
                    side_effect=RuntimeError("synthetic worker failure"),
                ),
            ):
                with self.assertRaises(RuntimeError):
                    touch_with_transaction_marker(
                        unit={},
                        stock_cpu=7,
                        page_size=4096,
                        page_index=1,
                        phase="NORMALIZE",
                        touch_number=1,
                        trial_id="0:0",
                        epoch=0,
                        trace_marker=marker,
                    )

        self.assertEqual(calls, ["PRE", "POST"])

    def test_observed_window_missing_is_fail_closed(self) -> None:
        w = observed_window(
            trace_text="",
            trial_id="0:0",
            epoch=0,
            phase="NORMALIZE",
            touch_number=1,
        )
        self.assertEqual(w["marker_error_count"], 1)
        self.assertEqual(w["pre_count"], 0)
        self.assertEqual(w["post_count"], 0)

    def test_receipt_readback_discovers_owner(self) -> None:
        text = """
x-1 [000] ... 50.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
worker-10 [007] ... 50.000000010: frl_pc_try64: counter=0xabc nr_pages=64 comm="memcg005gc_spaw"
worker-10 [007] ... 50.000000020: frl_refill_stock: memcg=0xdef nr_pages=63 comm="memcg005gc_spaw"
x-1 [000] ... 50.000000030: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
"""
        with tempfile.TemporaryDirectory() as td:
            trace_path = Path(td) / "trace.log"
            trace_path.write_text(text, encoding="utf-8")
            receipt = receipt_after_touch(
                trace_path=trace_path,
                trial_id="0:0",
                epoch=0,
                phase="NORMALIZE",
                touch_number=1,
                owner_counter=None,
            )

        self.assertTrue(receipt["trace_complete"])
        self.assertEqual(receipt["discovered_owner_counter"], "0xabc")
        self.assertEqual(receipt["page_counter_try_charge_64_count"], 1)
        self.assertEqual(receipt["refill_stock_63_count"], 1)


if __name__ == "__main__":
    unittest.main()
