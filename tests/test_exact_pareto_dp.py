from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.exact_pareto_dp import (
    dp_matches_cartesian_exact,
    exact_quotient_pareto_dp,
    work_statistics,
)
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups
from finite_ram_lab.stateoption_quotient import cadence_state_options


def option(
    state: str,
    name: str,
    *,
    ram: int,
    vram: int,
    traffic: int = 0,
    compute: int = 0,
    latency: int = 0,
    release: bool = False,
    release_proven: bool = False,
) -> StateOption:
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", float(ram)), ("VRAM", float(vram))),
        traffic_bytes=float(traffic),
        compute_cost=float(compute),
        latency_cost=float(latency),
        error_cost=0.0,
        releases_semantic_state=release,
        release_proven=release_proven,
    )


class ExactParetoDPTests(unittest.TestCase):
    def test_duplicate_provenance_is_preserved_without_duplicate_objective_state(self):
        groups = (
            (
                option("x", "a", ram=1, vram=1),
                option("x", "b", ram=1, vram=1),
                option("x", "c", ram=1, vram=1),
            ),
            (
                option("y", "d", ram=1, vram=1),
            ),
        )
        result = exact_quotient_pareto_dp(
            groups,
            {"RAM": 10, "VRAM": 10},
        )
        self.assertEqual(len(result.frontier), 1)
        self.assertEqual(result.provenance[0].equivalent_path_count, 3)

    def test_b436_plus_b447_matches_cartesian_exact(self):
        groups = mixed_option_groups() + (
            cadence_state_options(memory_high_mib=144),
        )
        capacities = {"RAM": 50000, "VRAM": 50000}
        self.assertTrue(
            dp_matches_cartesian_exact(groups, capacities)
        )
        stats = work_statistics(groups, capacities)
        self.assertEqual(stats["raw_cartesian_combinations"], 640)
        self.assertLess(stats["dp_total_expanded_states"], 640)

    def test_1000_random_stateoption_systems_match_cartesian_exact(self):
        rng = random.Random(458)
        capacities = {"RAM": 40, "VRAM": 40}

        for case in range(1000):
            groups = []
            for group_index in range(rng.randint(1, 4)):
                state = f"s{case}_{group_index}"
                group = [
                    option(
                        state,
                        "safe0",
                        ram=rng.randint(0, 20),
                        vram=rng.randint(0, 20),
                        traffic=rng.randint(0, 10),
                        compute=rng.randint(0, 10),
                        latency=rng.randint(0, 10),
                    )
                ]

                for option_index in range(1, rng.randint(2, 5)):
                    release = bool(rng.randrange(2))
                    release_proven = (not release) or bool(rng.randrange(2))
                    group.append(
                        option(
                            state,
                            f"o{option_index}",
                            ram=rng.randint(0, 20),
                            vram=rng.randint(0, 20),
                            traffic=rng.randint(0, 10),
                            compute=rng.randint(0, 10),
                            latency=rng.randint(0, 10),
                            release=release,
                            release_proven=release_proven,
                        )
                    )

                if rng.random() < 0.6:
                    source = rng.choice(group)
                    group.append(
                        StateOption(
                            state_name=state,
                            option_name=f"dup{group_index}",
                            resident_by_tier=source.resident_by_tier,
                            byte_seconds_by_tier=source.byte_seconds_by_tier,
                            traffic_bytes=source.traffic_bytes,
                            compute_cost=source.compute_cost,
                            latency_cost=source.latency_cost,
                            error_cost=source.error_cost,
                            releases_semantic_state=source.releases_semantic_state,
                            release_proven=source.release_proven,
                            merges_owners=source.merges_owners,
                            sharing_proven=source.sharing_proven,
                            error_bound_known=source.error_bound_known,
                        )
                    )
                groups.append(tuple(group))

            self.assertTrue(
                dp_matches_cartesian_exact(
                    tuple(groups),
                    capacities,
                )
            )


if __name__ == "__main__":
    unittest.main()
