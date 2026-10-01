from __future__ import annotations

import random
import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups
from finite_ram_lab.stateoption_quotient import (
    cadence_state_options,
    compilation_statistics,
    compile_state_option_group,
    quotient_preserves_exact_frontier,
)


def option(
    state: str,
    name: str,
    *,
    ram: int,
    vram: int,
    traffic: float = 0,
    compute: float = 0,
    latency: float = 0,
    error: float = 0,
    release: bool = False,
    release_proven: bool = False,
    merge: bool = False,
    sharing_proven: bool = False,
    error_bound_known: bool = True,
) -> StateOption:
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", float(ram)), ("VRAM", float(vram))),
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


class StateOptionQuotientTests(unittest.TestCase):
    def test_unsafe_option_is_removed_before_quotient(self):
        group = (
            option("x", "safe", ram=1, vram=1),
            option(
                "x",
                "unsafe",
                ram=0,
                vram=0,
                release=True,
                release_proven=False,
            ),
        )
        compiled = compile_state_option_group(
            group,
            {"RAM": 10, "VRAM": 10},
        )
        self.assertEqual(
            [item.option.option_name for item in compiled],
            ["safe"],
        )

    def test_equal_vector_different_semantic_signatures_do_not_collapse(self):
        group = (
            option("x", "retain", ram=1, vram=1),
            option(
                "x",
                "release",
                ram=1,
                vram=1,
                release=True,
                release_proven=True,
            ),
        )
        compiled = compile_state_option_group(
            group,
            {"RAM": 10, "VRAM": 10},
        )
        self.assertEqual(len(compiled), 2)
        self.assertEqual(
            {item.option.option_name for item in compiled},
            {"retain", "release"},
        )

    def test_equal_vector_same_signature_collapses_with_provenance(self):
        group = (
            option("x", "a", ram=1, vram=2),
            option("x", "b", ram=1, vram=2),
        )
        compiled = compile_state_option_group(
            group,
            {"RAM": 10, "VRAM": 10},
        )
        self.assertEqual(len(compiled), 1)
        self.assertEqual(compiled[0].provenance_option_names, ("a", "b"))

    def test_b447_cadence_group_reduces_five_to_three(self):
        group = cadence_state_options(memory_high_mib=144)
        compiled = compile_state_option_group(
            group,
            {"RAM": 1000, "VRAM": 1000},
        )
        self.assertEqual(
            {item.option.option_name for item in compiled},
            {
                "dontneed_32m",
                "dontneed_48m",
                "dontneed_96m",
            },
        )

    def test_b436_plus_b447_reduces_640_to_384_and_preserves_frontier(self):
        capacities = {"RAM": 50000, "VRAM": 50000}
        groups = mixed_option_groups() + (
            cadence_state_options(memory_high_mib=144),
        )
        stats = compilation_statistics(groups, capacities)
        self.assertEqual(stats["raw_combination_count"], 640)
        self.assertEqual(stats["compiled_combination_count"], 384)
        self.assertAlmostEqual(
            stats["combination_reduction_fraction"],
            0.4,
        )
        self.assertTrue(
            quotient_preserves_exact_frontier(groups, capacities)
        )

    def test_2000_random_stateoption_systems_preserve_exact_frontier_vectors(self):
        rng = random.Random(455)
        capacities = {"RAM": 30, "VRAM": 30}
        for case in range(2000):
            groups = []
            for group_index in range(rng.randint(1, 4)):
                group = []
                # Ensure at least one simple safe option exists.
                group.append(
                    option(
                        f"s{case}_{group_index}",
                        "safe0",
                        ram=rng.randint(0, 20),
                        vram=rng.randint(0, 20),
                        traffic=rng.randint(0, 10),
                        compute=rng.randint(0, 10),
                        latency=rng.randint(0, 10),
                    )
                )
                for option_index in range(1, rng.randint(2, 5)):
                    release = bool(rng.randrange(2))
                    release_proven = (not release) or bool(rng.randrange(2))
                    merge = bool(rng.randrange(2))
                    sharing = (not merge) or bool(rng.randrange(2))
                    error = float(rng.randint(0, 3))
                    error_known = (error == 0.0) or bool(rng.randrange(2))
                    group.append(
                        option(
                            f"s{case}_{group_index}",
                            f"o{option_index}",
                            ram=rng.randint(0, 20),
                            vram=rng.randint(0, 20),
                            traffic=rng.randint(0, 10),
                            compute=rng.randint(0, 10),
                            latency=rng.randint(0, 10),
                            error=error,
                            release=release,
                            release_proven=release_proven,
                            merge=merge,
                            sharing_proven=sharing,
                            error_bound_known=error_known,
                        )
                    )
                groups.append(tuple(group))

            self.assertTrue(
                quotient_preserves_exact_frontier(
                    tuple(groups),
                    capacities,
                )
            )


if __name__ == "__main__":
    unittest.main()
