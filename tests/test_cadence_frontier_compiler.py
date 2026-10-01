from __future__ import annotations

import random
import unittest

from finite_ram_lab.cadence_frontier_compiler import (
    brute_objective_frontier,
    brute_plan_frontier,
    compilation_summary,
    compile_cadence_classes,
    frontier_tie_groups,
    symbolic_frontier,
)


class CadenceFrontierCompilerTests(unittest.TestCase):
    def test_b447_classes(self):
        summary = compilation_summary(
            file_span_mib=96,
            cadences_mib=(32, 48, 64, 80, 96),
            transient_base_mib=78.609,
        )
        self.assertEqual(
            summary["representatives_mib"],
            (32, 48, 96),
        )
        self.assertEqual(
            summary["mechanism_only_mib"],
            (64, 80),
        )
        self.assertAlmostEqual(
            summary["search_reduction_fraction"],
            0.4,
        )
        self.assertEqual(
            summary["frontier_semantics"],
            "canonical objective-vector quotient",
        )

    def test_b447_symbolic_frontiers(self):
        classes = compile_cadence_classes(
            file_span_mib=96,
            cadences_mib=(32, 48, 64, 80, 96),
            transient_base_mib=78.609,
        )
        self.assertEqual(
            symbolic_frontier(memory_high_mib=100, classes=classes),
            (96,),
        )
        self.assertEqual(
            symbolic_frontier(memory_high_mib=120, classes=classes),
            (32, 96),
        )
        self.assertEqual(
            symbolic_frontier(memory_high_mib=144, classes=classes),
            (32, 48, 96),
        )

    def test_counterexample_distinguishes_plan_ids_from_objective_vectors(self):
        args = dict(
            file_span_mib=26,
            cadences_mib=(1, 3, 6, 8, 18, 21, 23),
            transient_base_mib=117.71505279868073,
            clean_floor_mib=7.332654536144995,
            memory_high_mib=86.03951733164814,
        )
        self.assertEqual(
            brute_plan_frontier(**args),
            (18, 21, 23),
        )
        self.assertEqual(
            frontier_tie_groups(**args),
            ((18, 21, 23),),
        )
        self.assertEqual(
            brute_objective_frontier(**args),
            (18,),
        )
        classes = compile_cadence_classes(
            file_span_mib=args["file_span_mib"],
            cadences_mib=args["cadences_mib"],
            transient_base_mib=args["transient_base_mib"],
        )
        self.assertEqual(
            symbolic_frontier(
                memory_high_mib=args["memory_high_mib"],
                classes=classes,
            ),
            (18,),
        )

    def test_20000_random_discrete_systems_preserve_objective_frontier(self):
        rng = random.Random(453)
        for _ in range(20_000):
            file_span = rng.randint(8, 256)
            population = list(range(1, file_span + 1))
            cadences = tuple(
                sorted(
                    rng.sample(
                        population,
                        rng.randint(1, min(12, len(population))),
                    )
                )
            )
            base = rng.uniform(1.0, 128.0)
            clean_floor = rng.uniform(0.0, base)
            classes = compile_cadence_classes(
                file_span_mib=float(file_span),
                cadences_mib=cadences,
                transient_base_mib=base,
            )
            high = rng.uniform(clean_floor + 1e-6, base + file_span + 64.0)
            self.assertEqual(
                symbolic_frontier(
                    memory_high_mib=high,
                    classes=classes,
                ),
                brute_objective_frontier(
                    file_span_mib=float(file_span),
                    cadences_mib=cadences,
                    transient_base_mib=base,
                    clean_floor_mib=clean_floor,
                    memory_high_mib=high,
                ),
            )


if __name__ == "__main__":
    unittest.main()
