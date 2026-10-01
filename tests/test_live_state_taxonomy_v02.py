from __future__ import annotations

import random
import unittest

from finite_ram_lab.live_state_taxonomy_v02 import (
    CONTROL_ORDER,
    EXEMPLAR_ACTIONS,
    PhysicalState,
    SemanticAction,
    SemanticState,
    ordered_control_stages,
    physical_resident_bytes_by_tier,
    semantic_release_action,
)


class LiveStateTaxonomyV02Tests(unittest.TestCase):
    def test_summary_precedes_rematerialization(self):
        state = SemanticState(
            "x",
            logical_bytes=100,
            owners=("stage0",),
            future_sufficient_summary_bytes=20,
            recomputable=True,
        )
        self.assertEqual(semantic_release_action(state), SemanticAction.REDUCE)

    def test_recomputable_without_summary_rematerializes(self):
        state = SemanticState(
            "x",
            logical_bytes=100,
            owners=("stage0",),
            recomputable=True,
        )
        self.assertEqual(
            semantic_release_action(state),
            SemanticAction.REMATERIALIZE,
        )

    def test_unknown_recoverability_retains(self):
        state = SemanticState(
            "x",
            logical_bytes=100,
            owners=("stage0",),
        )
        self.assertEqual(semantic_release_action(state), SemanticAction.RETAIN)

    def test_control_order_is_stable(self):
        actions = (
            "UNLOAD",
            "MOVE",
            "COMPRESS",
            "REDUCE",
            "BORROW",
            "SHARE",
            "REORDER",
        )
        self.assertEqual(
            ordered_control_stages(actions),
            (
                "SEMANTIC_REDUCTION",
                "OWNERSHIP",
                "REPRESENTATION",
                "TEMPORALIZATION",
                "PLACEMENT",
                "PHASE_BORROWING",
                "LIFETIME",
            ),
        )

    def test_tier_bytes_do_not_count_backing_only_state(self):
        states = [
            PhysicalState("weights", "iq3", "VRAM", "GGUF", 8),
            PhysicalState("weights", "iq3", "RAM", "GGUF", 12),
            PhysicalState("weights", "iq3", None, "GGUF", 0),
        ]
        self.assertEqual(
            physical_resident_bytes_by_tier(states),
            {"VRAM": 8, "RAM": 12},
        )

    def test_replica_count_is_physical_not_semantic(self):
        states = [
            PhysicalState(
                "dense",
                "bf16",
                "VRAM",
                "GGUF",
                100,
                replicas=2,
            )
        ]
        self.assertEqual(
            physical_resident_bytes_by_tier(states),
            {"VRAM": 200},
        )

    def test_cross_domain_exemplars_map_without_unknown_actions(self):
        for actions in EXEMPLAR_ACTIONS.values():
            ordered_control_stages(actions)

    def test_20000_random_action_orderings_are_monotone(self):
        rng = random.Random(433)
        actions = tuple({
            action
            for values in EXEMPLAR_ACTIONS.values()
            for action in values
        })
        for _ in range(20_000):
            chosen = [
                rng.choice(actions)
                for _ in range(rng.randint(0, 20))
            ]
            stages = ordered_control_stages(chosen)
            ranks = [CONTROL_ORDER[s] for s in stages]
            self.assertEqual(ranks, sorted(set(ranks)))


if __name__ == "__main__":
    unittest.main()
