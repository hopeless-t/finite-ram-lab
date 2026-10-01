from __future__ import annotations

import random
import unittest

from finite_ram_lab.option_quotient_compiler import (
    Choice,
    global_pareto_vectors,
    quotient_group,
    quotient_groups,
    quotient_statistics,
)


def choice(choice_id: str, *vector: float) -> Choice:
    return Choice(choice_id, tuple(float(value) for value in vector))


class OptionQuotientCompilerTests(unittest.TestCase):
    def test_exact_ties_keep_provenance(self):
        group = (
            choice("18", 10, 2),
            choice("21", 10, 2),
            choice("23", 10, 2),
        )
        compiled = quotient_group(group)
        self.assertEqual(len(compiled), 1)
        self.assertEqual(compiled[0].choice_id, "18")
        self.assertEqual(compiled[0].provenance, ("18", "21", "23"))

    def test_local_dominance_and_ties_reduce_combinations(self):
        groups = (
            (
                choice("a0", 1, 5),
                choice("a1", 2, 5),
                choice("a2", 4, 1),
                choice("a3", 4, 1),
                choice("a4", 5, 5),
            ),
            (
                choice("b0", 0, 3),
                choice("b1", 1, 2),
                choice("b2", 1, 2),
                choice("b3", 3, 0),
            ),
        )
        stats = quotient_statistics(groups)
        self.assertEqual(stats["raw_combination_count"], 20)
        self.assertEqual(stats["quotient_group_sizes"], (2, 3))
        self.assertEqual(stats["quotient_combination_count"], 6)
        self.assertAlmostEqual(stats["combination_reduction_fraction"], 0.7)

    def test_5000_random_additive_systems_preserve_global_pareto_vectors(self):
        rng = random.Random(454)
        for case in range(5000):
            dimensions = rng.randint(2, 5)
            groups = []
            for group_index in range(rng.randint(1, 4)):
                raw = []
                for option_index in range(rng.randint(1, 5)):
                    # Integer vectors deliberately generate exact ties.
                    vector = tuple(
                        float(rng.randint(0, 12))
                        for _ in range(dimensions)
                    )
                    raw.append(
                        Choice(
                            choice_id=f"g{case}_{group_index}_o{option_index}",
                            objective_vector=vector,
                        )
                    )
                groups.append(tuple(raw))

            full = global_pareto_vectors(tuple(groups))
            reduced = global_pareto_vectors(
                quotient_groups(tuple(groups))
            )
            self.assertEqual(reduced, full)


if __name__ == "__main__":
    unittest.main()
