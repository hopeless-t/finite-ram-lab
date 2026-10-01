from __future__ import annotations

import unittest

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.pareto_beam_controller import beam_pareto_controller
from finite_ram_lab.quotient_aware_beam import quotient_aware_beam_controller
from finite_ram_lab.stateoption_quotient import compiled_raw_groups


def option(
    state: str,
    name: str,
    vector: tuple[int, int, int, int, int],
    *,
    release: bool = False,
    release_proven: bool = False,
) -> StateOption:
    ram, vram, traffic, compute, latency = vector
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


def vectors(plans):
    return {
        plan.objective_vector(("RAM", "VRAM"))
        for plan in plans
    }


class QuotientAwareBeamTests(unittest.TestCase):
    def test_duplicate_multiplicity_does_not_change_objective_result(self):
        base = (
            (
                option("a", "a0", (1, 5, 4, 2, 2)),
                option("a", "a1", (5, 1, 1, 4, 3)),
            ),
            (
                option("b", "b0", (2, 2, 5, 1, 4)),
                option("b", "b1", (3, 3, 1, 5, 1)),
            ),
            (
                option("c", "c0", (1, 4, 2, 3, 5)),
                option("c", "c1", (4, 1, 3, 2, 1)),
            ),
        )
        duplicate_heavy = (
            base[0] + tuple(
                option("a", f"a0_dup{i}", (1, 5, 4, 2, 2))
                for i in range(20)
            ),
            base[1],
            base[2],
        )
        capacities = {"RAM": 100, "VRAM": 100}

        clean = quotient_aware_beam_controller(
            base,
            capacities,
            beam_width=8,
        )
        heavy = quotient_aware_beam_controller(
            duplicate_heavy,
            capacities,
            beam_width=8,
        )

        self.assertEqual(
            vectors(clean.frontier),
            vectors(heavy.frontier),
        )
        self.assertGreater(
            heavy.depth_stats[0].pareto_states_before_quotient,
            heavy.depth_stats[0].quotient_states,
        )

    def test_same_vector_different_semantics_do_not_merge(self):
        groups = (
            (
                option("x", "retain", (1, 1, 0, 0, 0)),
                option(
                    "x",
                    "release",
                    (1, 1, 0, 0, 0),
                    release=True,
                    release_proven=True,
                ),
            ),
            (
                option("y", "y0", (1, 1, 0, 0, 0)),
            ),
        )
        result = quotient_aware_beam_controller(
            groups,
            {"RAM": 10, "VRAM": 10},
            beam_width=8,
        )
        self.assertEqual(
            result.depth_stats[0].quotient_states,
            2,
        )

    def test_raw_input_matches_precompiled_objective_frontier(self):
        groups = (
            (
                option("a", "a0", (1, 5, 4, 2, 2)),
                option("a", "a0_dup", (1, 5, 4, 2, 2)),
                option("a", "a1", (5, 1, 1, 4, 3)),
                option("a", "dom", (8, 8, 9, 9, 9)),
            ),
            (
                option("b", "b0", (2, 2, 5, 1, 4)),
                option("b", "b1", (3, 3, 1, 5, 1)),
            ),
            (
                option("c", "c0", (1, 4, 2, 3, 5)),
                option("c", "c1", (4, 1, 3, 2, 1)),
            ),
        )
        capacities = {"RAM": 100, "VRAM": 100}
        compiled = compiled_raw_groups(groups, capacities)

        aware = quotient_aware_beam_controller(
            groups,
            capacities,
            beam_width=8,
        )
        precompiled = beam_pareto_controller(
            compiled,
            capacities,
            beam_width=8,
        )
        self.assertEqual(
            vectors(aware.frontier),
            vectors(precompiled),
        )

    def test_factorized_provenance_records_tied_source_options(self):
        groups = (
            (
                option("x", "a", (1, 1, 0, 0, 0)),
                option("x", "b", (1, 1, 0, 0, 0)),
                option("x", "c", (1, 1, 0, 0, 0)),
            ),
            (
                option("y", "d", (1, 1, 0, 0, 0)),
            ),
        )
        result = quotient_aware_beam_controller(
            groups,
            {"RAM": 10, "VRAM": 10},
            beam_width=8,
        )
        self.assertEqual(len(result.provenance), 1)
        mapping = dict(result.provenance[0].provenance_by_state)
        self.assertEqual(mapping["x"], ("a", "b", "c"))
        self.assertEqual(result.provenance[0].equivalent_path_count, 3)


if __name__ == "__main__":
    unittest.main()
