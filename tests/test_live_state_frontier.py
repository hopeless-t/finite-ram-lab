from __future__ import annotations

import math
import random
import unittest

from finite_ram_lab.live_state_frontier import (
    ReleaseMode,
    State,
    exact_fast_residency,
    greedy_fast_residency,
    release_net_benefit,
    resident_value_density,
    safe_release_mode,
)


def state(name="s", **overrides):
    values = {
        "name": name,
        "size_bytes": 100,
        "expected_accesses": 2.0,
        "fast_access_cost": 1.0,
        "slow_access_cost": 5.0,
        "recompute_cost": 7.0,
        "recomputable": False,
        "summary_bytes": None,
        "summary_sufficient": False,
    }
    values.update(overrides)
    return State(**values)


class LiveStateFrontierTests(unittest.TestCase):
    def test_future_sufficient_summary_is_strongest_release(self):
        s = state(summary_bytes=12, summary_sufficient=True, recomputable=True)
        self.assertEqual(safe_release_mode(s), ReleaseMode.REDUCE_AND_RELEASE)

    def test_recomputable_state_can_drop(self):
        self.assertEqual(
            safe_release_mode(state(recomputable=True)),
            ReleaseMode.DROP_REMATERIALIZE,
        )

    def test_unknown_recoverability_fails_closed(self):
        self.assertEqual(
            safe_release_mode(state()),
            ReleaseMode.RETAIN_OR_MOVE,
        )

    def test_equal_size_summary_does_not_count_as_reduction(self):
        self.assertEqual(
            safe_release_mode(state(summary_bytes=100, summary_sufficient=True)),
            ReleaseMode.RETAIN_OR_MOVE,
        )

    def test_resident_value_density(self):
        s = state(
            size_bytes=8,
            expected_accesses=4,
            fast_access_cost=1,
            slow_access_cost=5,
        )
        self.assertEqual(resident_value_density(s), 2.0)

    def test_summary_release_exchange_inequality(self):
        s = state(size_bytes=100, summary_bytes=20, summary_sufficient=True)
        result = release_net_benefit(
            s,
            shadow_price_per_byte_second=0.5,
            horizon_seconds=10,
            transform_cost=15,
        )
        self.assertEqual(result, 385.0)

    def test_rematerialization_release_exchange_inequality(self):
        s = state(
            size_bytes=100,
            expected_accesses=2,
            recompute_cost=30,
            recomputable=True,
        )
        result = release_net_benefit(
            s,
            shadow_price_per_byte_second=0.1,
            horizon_seconds=10,
        )
        self.assertEqual(result, 40.0)

    def test_no_safe_release_is_negative_infinity(self):
        value = release_net_benefit(
            state(),
            shadow_price_per_byte_second=1,
            horizon_seconds=1,
        )
        self.assertTrue(math.isinf(value))
        self.assertLess(value, 0)

    def test_exact_residency_known_optimum(self):
        states = [
            state(
                "hot-small",
                size_bytes=3,
                expected_accesses=20,
                fast_access_cost=1,
                slow_access_cost=10,
            ),
            state(
                "warm-mid",
                size_bytes=5,
                expected_accesses=10,
                fast_access_cost=1,
                slow_access_cost=8,
            ),
            state(
                "cold-big",
                size_bytes=9,
                expected_accesses=1,
                fast_access_cost=1,
                slow_access_cost=10,
            ),
        ]
        result = exact_fast_residency(states, 8)
        self.assertEqual(result["resident"], ["hot-small", "warm-mid"])
        self.assertEqual(result["used_bytes"], 8)
        self.assertEqual(result["expected_access_savings"], 250.0)

    def test_greedy_never_exceeds_capacity_in_fuzz(self):
        rng = random.Random(426)
        for case in range(20_000):
            count = rng.randint(0, 20)
            states = [
                state(
                    f"s{case}_{i}",
                    size_bytes=rng.randint(1, 1000),
                    expected_accesses=rng.random() * 100,
                    fast_access_cost=rng.random() * 5,
                    slow_access_cost=5 + rng.random() * 20,
                )
                for i in range(count)
            ]
            capacity = rng.randint(0, 5000)
            result = greedy_fast_residency(states, capacity)
            self.assertLessEqual(result["used_bytes"], capacity)

    def test_exact_not_worse_than_greedy_in_small_fuzz(self):
        rng = random.Random(427)
        for case in range(2_000):
            count = rng.randint(0, 12)
            states = [
                state(
                    f"s{case}_{i}",
                    size_bytes=rng.randint(1, 50),
                    expected_accesses=rng.random() * 20,
                    fast_access_cost=rng.random() * 3,
                    slow_access_cost=3 + rng.random() * 10,
                )
                for i in range(count)
            ]
            capacity = rng.randint(0, 150)
            exact = exact_fast_residency(states, capacity)
            greedy = greedy_fast_residency(states, capacity)
            self.assertGreaterEqual(
                exact["expected_access_savings"] + 1e-9,
                greedy["expected_access_savings"],
            )


if __name__ == "__main__":
    unittest.main()
