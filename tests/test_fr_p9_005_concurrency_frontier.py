import unittest

from finite_ram_lab.fr_p9_005_concurrency_frontier import (
    pareto_workers,
    run_synthetic_panel,
    summarize_runs,
)


class FrP9005ConcurrencyFrontierTests(unittest.TestCase):
    def test_synthetic_panel_passes(self) -> None:
        panel = run_synthetic_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertEqual(panel["pareto_worker_counts"], [1, 2, 4])
        self.assertIsNone(panel["scalar_gain"])

    def test_dominated_worker_is_removed(self) -> None:
        rows = [
            {
                "workers": 1,
                "median_total_pss_kib": 10,
                "median_wall_ns": 100,
                "median_p95_queue_wait_ns": 80,
                "median_p95_service_ns": 20,
                "median_p95_sojourn_ns": 100,
            },
            {
                "workers": 2,
                "median_total_pss_kib": 20,
                "median_wall_ns": 90,
                "median_p95_queue_wait_ns": 60,
                "median_p95_service_ns": 30,
                "median_p95_sojourn_ns": 90,
            },
            {
                "workers": 4,
                "median_total_pss_kib": 30,
                "median_wall_ns": 120,
                "median_p95_queue_wait_ns": 70,
                "median_p95_service_ns": 40,
                "median_p95_sojourn_ns": 120,
            },
        ]
        self.assertEqual(pareto_workers(rows), [1, 2])

    def test_summary_preserves_digest_identity(self) -> None:
        digests = {"0": "a", "1": "b"}
        rows = [
            {
                "workers": 2,
                "total_pss_kib": 100,
                "wall_ns": 200,
                "jobs_per_second": 10.0,
                "p95_queue_wait_ns": 30,
                "p95_service_ns": 40,
                "p95_sojourn_ns": 70,
                "digests": digests,
            },
            {
                "workers": 2,
                "total_pss_kib": 120,
                "wall_ns": 180,
                "jobs_per_second": 11.0,
                "p95_queue_wait_ns": 20,
                "p95_service_ns": 50,
                "p95_sojourn_ns": 65,
                "digests": digests,
            },
        ]
        summary = summarize_runs(rows, workers=2)
        self.assertTrue(summary["semantic_stable_within_worker_count"])
        self.assertEqual(summary["median_total_pss_kib"], 110)
        self.assertEqual(summary["digests"], digests)

    def test_missing_worker_count_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            summarize_runs([], workers=4)


if __name__ == "__main__":
    unittest.main()
