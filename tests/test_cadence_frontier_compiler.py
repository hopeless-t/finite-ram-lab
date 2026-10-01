from __future__ import annotations

import random
import unittest

from finite_ram_lab.cadence_frontier_compiler import (
    brute_frontier,
    compilation_summary,
    compile_cadence_classes,
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

    def test_20000_random_discrete_systems_match_bruteforce(self):
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
                brute_frontier(
                    file_span_mib=float(file_span),
                    cadences_mib=cadences,
                    transient_base_mib=base,
                    clean_floor_mib=clean_floor,
                    memory_high_mib=high,
                ),
            )


if __name__ == "__main__":
    unittest.main()
