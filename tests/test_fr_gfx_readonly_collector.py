from __future__ import annotations

import io
import json
import os
import unittest

from finite_ram_lab.fr_gfx_readonly_collector import (
    collect_once,
    run_collection,
)


class FrGfxReadonlyCollectorTests(
    unittest.TestCase
):
    def test_collect_self(self):
        row = collect_once(
            os.getpid()
        )

        self.assertEqual(
            row["target_pid"],
            os.getpid(),
        )

        self.assertIsNotNone(
            row[
                "system"
            ][
                "mem_available_kib"
            ]
        )

        self.assertIsNotNone(
            row[
                "process"
            ]["rss_kib"]
        )

    def test_short_collection_emits_jsonl(self):
        output = io.StringIO()

        receipt = run_collection(
            target_pid=os.getpid(),
            samples=3,
            interval_ms=0.0,
            output=output,
        )

        lines = [
            line
            for line in (
                output.getvalue()
                .splitlines()
            )
            if line
        ]

        self.assertEqual(
            len(lines),
            3,
        )

        for line in lines:
            row = json.loads(
                line
            )

            self.assertEqual(
                row[
                    "target_pid"
                ],
                os.getpid(),
            )

        self.assertGreater(
            receipt[
                "jsonl_bytes"
            ],
            0,
        )

    def test_read_only_contract(self):
        output = io.StringIO()

        receipt = run_collection(
            target_pid=os.getpid(),
            samples=1,
            interval_ms=0.0,
            output=output,
        )

        contract = receipt[
            "read_only_contract"
        ]

        for key in (
            "writes_sysfs",
            "changes_game_settings",
            "changes_driver_settings",
            "injects_target_process",
            "signals_target_process",
            "launches_gpu_telemetry",
            "launches_frame_telemetry",
        ):
            self.assertFalse(
                contract[key]
            )

        self.assertTrue(
            contract[
                "writes_only_requested_output_stream"
            ]
        )

    def test_no_live_threshold_claim(self):
        output = io.StringIO()

        receipt = run_collection(
            target_pid=os.getpid(),
            samples=1,
            interval_ms=0.0,
            output=output,
        )

        self.assertEqual(
            receipt[
                "qualification"
            ],
            "MEASUREMENT_ONLY_NO_LIVE_PERTURBATION_THRESHOLD",
        )


if __name__ == "__main__":
    unittest.main()
