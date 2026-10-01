from __future__ import annotations

import random
import unittest

from finite_ram_lab.axis_temporalization import (
    AxisModel,
    best_plan,
    classify_memory_move,
    enumerate_feasible_plans,
    invocation_count,
    normalized_workspace,
)


class AxisTemporalizationTests(unittest.TestCase):
    def test_precision_axis_fails_closed_without_proof(self):
        model = AxisModel(8, 8, 8, 8, memory_limit_bytes=1000)
        with self.assertRaisesRegex(ValueError, "precision_temporalization_unproven"):
            normalized_workspace(model, 4, 4, 4, 4)

    def test_precision_axis_can_open_new_feasible_region_with_proof(self):
        unproven = AxisModel(8, 8, 8, 8, memory_limit_bytes=20)
        proven = AxisModel(
            8, 8, 8, 8,
            memory_limit_bytes=20,
            precision_streaming_proven=True,
        )
        self.assertEqual(enumerate_feasible_plans(unproven), ())
        self.assertTrue(enumerate_feasible_plans(proven))
        self.assertTrue(
            any(p.precision_temporalized for p in enumerate_feasible_plans(proven))
        )

    def test_full_tile_is_one_invocation(self):
        model = AxisModel(8, 8, 8, 8, memory_limit_bytes=2000)
        self.assertEqual(invocation_count(model, 8, 8, 8, 8), 1)
        plan = best_plan(model)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual((plan.bm, plan.bn, plan.bk, plan.bp), (8, 8, 8, 8))
        self.assertEqual(plan.invocations, 1)

    def test_memory_exchange_classification(self):
        self.assertEqual(
            classify_memory_move(
                peak_delta=-1,
                traffic_delta=2,
                compute_delta=0,
                latency_delta=1,
                error_delta=0,
            ),
            "MEMORY_EXCHANGE",
        )

    def test_pareto_improvement_classification(self):
        self.assertEqual(
            classify_memory_move(
                peak_delta=-1,
                traffic_delta=-2,
                compute_delta=0,
                latency_delta=-1,
                error_delta=0,
            ),
            "PARETO_IMPROVEMENT",
        )

    def test_10000_random_feasible_plans_respect_limit_and_proof(self):
        rng = random.Random(430)
        for _ in range(10_000):
            m = rng.randint(1, 24)
            n = rng.randint(1, 24)
            k = rng.randint(1, 24)
            p = rng.randint(1, 12)
            limit = rng.randint(1, 20_000)
            proven = bool(rng.randrange(2))
            model = AxisModel(
                m, n, k, p,
                memory_limit_bytes=limit,
                precision_streaming_proven=proven,
            )
            for plan in enumerate_feasible_plans(model):
                self.assertLessEqual(plan.workspace_bytes, limit)
                if plan.bp < p:
                    self.assertTrue(proven)
                self.assertEqual(
                    plan.invocations,
                    invocation_count(
                        model, plan.bm, plan.bn, plan.bk, plan.bp
                    ),
                )

    def test_best_plan_is_minimum_invocation_count(self):
        rng = random.Random(431)
        for _ in range(2_000):
            model = AxisModel(
                rng.randint(1, 16),
                rng.randint(1, 16),
                rng.randint(1, 16),
                rng.randint(1, 8),
                memory_limit_bytes=rng.randint(1, 5000),
                precision_streaming_proven=bool(rng.randrange(2)),
            )
            plans = enumerate_feasible_plans(model)
            best = best_plan(model)
            if not plans:
                self.assertIsNone(best)
            else:
                self.assertIsNotNone(best)
                assert best is not None
                self.assertEqual(
                    best.invocations,
                    min(p.invocations for p in plans),
                )


if __name__ == "__main__":
    unittest.main()
