from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.capacity_phase_diagram import (
    frontier_is_monotone_under_capacity_expansion,
    neighboring_transitions,
    phase_grid,
    signature_delta,
    unique_regime_count,
)
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups


def option(state, name, *, ram, vram, traffic=0, compute=0, latency=0):
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", ram), ("VRAM", vram)),
        traffic_bytes=traffic,
        compute_cost=compute,
        latency_cost=latency,
    )


class CapacityPhaseDiagramTests(unittest.TestCase):
    VRAM = (
        9216, 9728, 10240, 10752, 11264,
        12288, 13312, 14336, 16384, 18432,
        20480, 22528, 24576, 28672, 32768,
    )
    RAM = (
        8192, 9216, 10240, 12288, 14336,
        16384, 20480, 24576, 28672, 32768, 40960,
    )

    def test_b436_grid_has_19_nonempty_strategy_regimes(self):
        cells = phase_grid(
            mixed_option_groups(),
            ram_capacities_mib=self.RAM,
            vram_capacities_mib=self.VRAM,
        )
        self.assertEqual(unique_regime_count(cells), 19)

    def test_capacity_expansion_never_removes_visible_option_on_b436_grid(self):
        cells = phase_grid(
            mixed_option_groups(),
            ram_capacities_mib=self.RAM,
            vram_capacities_mib=self.VRAM,
        )
        transitions = neighboring_transitions(
            cells,
            ram_capacities_mib=self.RAM,
            vram_capacities_mib=self.VRAM,
        )
        self.assertEqual(len(transitions), 102)
        self.assertTrue(all(not transition.removed for transition in transitions))

    def test_signature_delta_reports_additions(self):
        before = (
            ("semantic", ("reduce",)),
            ("kv", ("stream",)),
        )
        after = (
            ("semantic", ("materialize", "reduce")),
            ("kv", ("full", "stream")),
        )
        added, removed = signature_delta(before, after)
        self.assertEqual(
            dict(added),
            {"kv": ("full",), "semantic": ("materialize",)},
        )
        self.assertEqual(removed, ())

    def test_fixed_capacity_expansion_preserves_exact_pareto_plans(self):
        groups = mixed_option_groups()
        self.assertTrue(
            frontier_is_monotone_under_capacity_expansion(
                groups,
                {"RAM": 9776, "VRAM": 9356},
                {"RAM": 32768, "VRAM": 32768},
            )
        )

    def test_5000_random_static_instances_preserve_frontier_monotonicity(self):
        rng = random.Random(438)

        for case in range(5000):
            groups = []
            for state_index in range(rng.randint(1, 4)):
                group = []
                for option_index in range(rng.randint(1, 4)):
                    group.append(
                        option(
                            f"s{case}_{state_index}",
                            f"o{option_index}",
                            ram=rng.randint(0, 20),
                            vram=rng.randint(0, 20),
                            traffic=rng.randint(0, 20),
                            compute=rng.randint(0, 20),
                            latency=rng.randint(0, 20),
                        )
                    )
                groups.append(group)

            small = {
                "RAM": rng.randint(0, 30),
                "VRAM": rng.randint(0, 30),
            }
            large = {
                "RAM": small["RAM"] + rng.randint(0, 20),
                "VRAM": small["VRAM"] + rng.randint(0, 20),
            }

            self.assertTrue(
                frontier_is_monotone_under_capacity_expansion(
                    groups,
                    small,
                    large,
                )
            )


if __name__ == "__main__":
    unittest.main()
