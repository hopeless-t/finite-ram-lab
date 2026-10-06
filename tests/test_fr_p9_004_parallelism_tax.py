import unittest

from finite_ram_lab.fr_p9_004_parallelism_tax import (
    run_synthetic_panel,
    summarize_repetitions,
)


class FrP9004ParallelismTaxTests(unittest.TestCase):
    def test_synthetic_panel_passes(self) -> None:
        panel = run_synthetic_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertTrue(all(panel["checks"].values()))

    def test_baseline_subtraction_preserves_capability_growth(self) -> None:
        rows = [
            {
                "mode": "BASELINE",
                "workers": 4,
                "total_pss_kib": 40000,
                "semantic_digest_exact": True,
            },
            {
                "mode": "PRIVATE_COPY",
                "workers": 4,
                "total_pss_kib": 104000,
                "semantic_digest_exact": True,
            },
            {
                "mode": "SHARED_MMAP",
                "workers": 4,
                "total_pss_kib": 57000,
                "semantic_digest_exact": True,
            },
        ]
        summary = summarize_repetitions(rows, workers=4)
        self.assertEqual(
            summary["normalized_growth_kib"]["PRIVATE_COPY"],
            64000,
        )
        self.assertEqual(
            summary["normalized_growth_kib"]["SHARED_MMAP"],
            17000,
        )
        self.assertTrue(summary["semantic_digest_exact"])

    def test_worker_count_mismatch_fails_closed(self) -> None:
        rows = [
            {
                "mode": "BASELINE",
                "workers": 1,
                "total_pss_kib": 100,
                "semantic_digest_exact": True,
            },
            {
                "mode": "PRIVATE_COPY",
                "workers": 4,
                "total_pss_kib": 200,
                "semantic_digest_exact": True,
            },
            {
                "mode": "SHARED_MMAP",
                "workers": 4,
                "total_pss_kib": 150,
                "semantic_digest_exact": True,
            },
        ]
        with self.assertRaises(ValueError):
            summarize_repetitions(rows, workers=4)

    def test_missing_mode_fails_closed(self) -> None:
        rows = [
            {
                "mode": "BASELINE",
                "workers": 1,
                "total_pss_kib": 100,
                "semantic_digest_exact": True,
            },
            {
                "mode": "PRIVATE_COPY",
                "workers": 1,
                "total_pss_kib": 200,
                "semantic_digest_exact": True,
            },
        ]
        with self.assertRaises(ValueError):
            summarize_repetitions(rows, workers=1)


if __name__ == "__main__":
    unittest.main()
