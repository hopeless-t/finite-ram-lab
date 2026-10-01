from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import (
    StateOption,
    exact_pareto_controller,
    dominates,
    plan_is_feasible,
)
from finite_ram_lab.pareto_beam_controller import (
    beam_pareto_controller,
    frontier_recovery_metrics,
)


def option(
    state,
    name,
    rng=None,
    *,
    vram=0,
    ram=0,
    vram_area=0,
    ram_area=0,
    traffic=0,
    compute=0,
    latency=0,
    error=0,
    release=False,
    release_proven=False,
    merge=False,
    sharing_proven=False,
    error_bound_known=True,
):
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", ram_area), ("VRAM", vram_area)),
        traffic_bytes=traffic,
        compute_cost=compute,
        latency_cost=latency,
        error_cost=error,
        releases_semantic_state=release,
        release_proven=release_proven,
        merges_owners=merge,
        sharing_proven=sharing_proven,
        error_bound_known=error_bound_known,
    )


def random_option(rng, state, name):
    error = rng.random() * 2 if rng.randrange(3) == 0 else 0.0
    release = bool(rng.randrange(2))
    merge = bool(rng.randrange(2))
    return option(
        state,
        name,
        vram=rng.randint(0, 20),
        ram=rng.randint(0, 20),
        vram_area=rng.randint(0, 100),
        ram_area=rng.randint(0, 100),
        traffic=rng.randint(0, 30),
        compute=rng.randint(0, 30),
        latency=rng.randint(0, 30),
        error=error,
        release=release,
        release_proven=(not release) or bool(rng.randrange(2)),
        merge=merge,
        sharing_proven=(not merge) or bool(rng.randrange(2)),
        error_bound_known=(error == 0.0) or bool(rng.randrange(2)),
    )


class ParetoBeamControllerTests(unittest.TestCase):
    def test_large_beam_matches_exact_small_problem(self):
        groups = [
            [
                option("a", "gpu", vram=5, vram_area=10),
                option("a", "ram", ram=5, ram_area=10, latency=1),
            ],
            [
                option("b", "fast", vram=4, vram_area=8),
                option("b", "small", vram=2, vram_area=4, compute=2),
            ],
        ]
        capacities = {"RAM": 8, "VRAM": 8}
        exact = exact_pareto_controller(groups, capacities)
        approx = beam_pareto_controller(groups, capacities, beam_width=64)
        self.assertEqual(
            {p.objective_vector(("RAM", "VRAM")) for p in approx},
            {p.objective_vector(("RAM", "VRAM")) for p in exact},
        )

    def test_unsafe_only_group_returns_empty(self):
        groups = [[
            option(
                "x",
                "unsafe",
                vram=1,
                release=True,
                release_proven=False,
            )
        ]]
        self.assertEqual(
            beam_pareto_controller(
                groups,
                {"RAM": 1, "VRAM": 1},
            ),
            (),
        )

    def test_capacity_is_never_repaired_by_flattening_tiers(self):
        groups = [[
            option("x", "gpu", vram=9),
            option("x", "ram", ram=9),
        ]]
        result = beam_pareto_controller(
            groups,
            {"RAM": 10, "VRAM": 4},
        )
        self.assertEqual([p.choices for p in result], [(("x", "ram"),)])

    def test_self_recovery_metrics_are_exact(self):
        groups = [[
            option("x", "resident", vram=8),
            option("x", "offload", vram=2, ram=8, traffic=2),
        ]]
        capacities = {"RAM": 16, "VRAM": 8}
        exact = exact_pareto_controller(groups, capacities)
        metrics = frontier_recovery_metrics(
            exact,
            exact,
            ("RAM", "VRAM"),
        )
        self.assertEqual(metrics["exact_point_coverage"], 1.0)
        self.assertEqual(metrics["approx_dominated_fraction"], 0.0)
        self.assertEqual(metrics["max_domination_gap"], 0.0)

    def test_1000_random_large_beam_matches_exact(self):
        rng = random.Random(43501)
        for case in range(1000):
            groups = []
            for state_index in range(rng.randint(1, 4)):
                groups.append([
                    random_option(
                        rng,
                        f"s{case}_{state_index}",
                        f"o{option_index}",
                    )
                    for option_index in range(rng.randint(1, 4))
                ])
            capacities = {
                "RAM": rng.randint(10, 40),
                "VRAM": rng.randint(10, 40),
            }
            exact = exact_pareto_controller(groups, capacities)
            approx = beam_pareto_controller(
                groups,
                capacities,
                beam_width=4096,
            )
            self.assertEqual(
                {p.objective_vector(("RAM", "VRAM")) for p in approx},
                {p.objective_vector(("RAM", "VRAM")) for p in exact},
            )

    def test_5000_random_width64_outputs_are_feasible_and_internal_pareto(self):
        rng = random.Random(43502)
        for case in range(5000):
            groups = []
            for state_index in range(rng.randint(2, 5)):
                groups.append([
                    random_option(
                        rng,
                        f"s{case}_{state_index}",
                        f"o{option_index}",
                    )
                    for option_index in range(rng.randint(2, 5))
                ])
            capacities = {
                "RAM": rng.randint(15, 50),
                "VRAM": rng.randint(15, 50),
            }
            approx = beam_pareto_controller(
                groups,
                capacities,
                beam_width=64,
            )
            for plan in approx:
                self.assertTrue(plan_is_feasible(plan, capacities))
            tiers = ("RAM", "VRAM")
            for i, plan in enumerate(approx):
                self.assertFalse(
                    any(
                        j != i and dominates(other, plan, tiers)
                        for j, other in enumerate(approx)
                    )
                )


if __name__ == "__main__":
    unittest.main()
