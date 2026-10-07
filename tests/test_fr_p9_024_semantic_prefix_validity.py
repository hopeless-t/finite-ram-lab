from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_024_semantic_prefix_validity import (
    PrefixAtom,
    compile_release_schedule,
    dependency_adversary,
    run_panel,
)


class SemanticPrefixValidityTests(unittest.TestCase):
    def test_dependency_and_verification_delay_semantic_release(self) -> None:
        result = dependency_adversary()
        self.assertEqual(result["chunk0_naive_release"], 1)
        self.assertEqual(result["chunk0_semantic_release"], 4)
        self.assertEqual(result["independent_semantic_release"], 2)

    def test_unknown_dependency_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            compile_release_schedule((PrefixAtom("a", 1, requires=("missing",)),))

    def test_cycle_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            compile_release_schedule(
                (
                    PrefixAtom("a", 1, requires=("b",)),
                    PrefixAtom("b", 1, requires=("a",)),
                )
            )

    def test_frozen_panel_passes(self) -> None:
        result = run_panel(seed=20261008, trials=1000)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exhaustive"]["mismatches"], 0)
        self.assertGreater(result["monte_carlo"]["naive_early_releases"], 0)
        self.assertEqual(result["monte_carlo"]["semantic_false_early_releases"], 0)
        self.assertIsNone(result["scalar_gain"])


if __name__ == "__main__":
    unittest.main()
