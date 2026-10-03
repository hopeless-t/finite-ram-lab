from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_observation_plane import (
    normalize_observation,
    parse_kib_table,
    parse_psi,
    run_panel,
)


class FrGfxObservationPlaneTests(
    unittest.TestCase
):
    def test_meminfo_parser(self):
        row = parse_kib_table(
            "MemAvailable: 1234 kB\n"
            "SwapFree: 567 kB\n"
        )

        self.assertEqual(
            row["MemAvailable"],
            1234,
        )
        self.assertEqual(
            row["SwapFree"],
            567,
        )

    def test_psi_parser(self):
        row = parse_psi(
            "some avg10=1.25 avg60=0.5 total=99\n"
            "full avg10=0.25 avg60=0.1 total=10\n"
        )

        self.assertEqual(
            row["some_avg10"],
            1.25,
        )
        self.assertEqual(
            row["full_avg10"],
            0.25,
        )

    def test_normalized_fixture_shape(self):
        row = normalize_observation(
            timestamp_ns=1,
            frame_ms=100.0,
            fps=10.0,
            meminfo_text=(
                "MemTotal: 1000 kB\n"
                "MemAvailable: 500 kB\n"
            ),
            smaps_rollup_text=(
                "Rss: 100 kB\n"
                "Pss: 80 kB\n"
            ),
            psi_memory_text=(
                "some avg10=0.5 total=1\n"
                "full avg10=0.0 total=0\n"
            ),
            intel_gpu_sample={
                "render_busy_pct": 90.0,
            },
            backend={
                "translation": "DXVK",
                "api": "D3D11",
            },
        )

        self.assertEqual(
            row["frame"]["fps"],
            10.0,
        )
        self.assertEqual(
            row["process"]["rss_kib"],
            100,
        )

    def test_multi_signal_accuracy_is_high(self):
        result = run_panel()

        self.assertGreater(
            result[
                "synthetic_identifiability"
            ][
                "multi_signal"
            ][
                "action_accuracy"
            ],
            0.94,
        )

    def test_matched_recall_false_positive_reduction(self):
        result = run_panel()
        panel = result[
            "synthetic_identifiability"
        ]

        self.assertEqual(
            panel[
                "fps_only"
            ]["gpu_bound_recall"],
            panel[
                "multi_signal"
            ]["gpu_bound_recall"],
        )

        self.assertGreater(
            panel[
                "fps_only"
            ][
                "gpu_downscale_false_positive_rate"
            ],
            0.30,
        )

        self.assertEqual(
            panel[
                "multi_signal"
            ][
                "gpu_downscale_false_positive_rate"
            ],
            0.0,
        )

    def test_observer_is_read_only_by_contract(self):
        result = run_panel()
        contract = result[
            "read_only_contract"
        ]

        self.assertTrue(
            all(
                value is False
                for value
                in contract.values()
            )
        )

    def test_claim_ceiling(self):
        result = run_panel()

        self.assertEqual(
            result["claim_ceiling"],
            "READ_ONLY_SCHEMA_AND_SYNTHETIC_IDENTIFIABILITY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
