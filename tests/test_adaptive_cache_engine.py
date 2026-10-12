from __future__ import annotations

import random
import unittest

from finite_ram_lab.adaptive_cache_engine import prepare_trace
from finite_ram_lab.sim import generate_trace, lru_faults, opt_faults


class AdaptiveCacheEngineTests(unittest.TestCase):
    def test_reference_parity_all_families(self) -> None:
        families = ["stable_hotset", "sequential_scan", "shifting_hotset", "bursty"]
        for family in families:
            for seed in range(4):
                trace = generate_trace(family, random.Random(1000 + seed), 1200, 73, 17)
                prepared = prepare_trace(trace)
                caps = [1, 3, 7, 17, 31, 63]
                for backend in ["python", "auto"]:
                    lru = prepared.lru_sweep(caps, backend=backend)
                    opt = prepared.opt_sweep(caps, backend=backend, workers=1)
                    self.assertEqual(lru, {c: lru_faults(trace, c) for c in caps})
                    self.assertEqual(opt, {c: opt_faults(trace, c) for c in caps})

    def test_arbitrary_hashable_pages(self) -> None:
        trace = ["a", "b", "a", "c", "a", "b", "d", "a"]
        prepared = prepare_trace(trace)
        self.assertEqual(prepared.unique_pages, 4)
        self.assertEqual(prepared.faults("lru", 2), lru_faults(trace, 2))
        self.assertEqual(prepared.faults("opt", 2), opt_faults(trace, 2))

    def test_compare_and_minimum_capacity(self) -> None:
        trace = [0, 1, 2, 0, 1, 2, 0, 1, 2]
        prepared = prepare_trace(trace)
        rows = prepared.compare([1, 2, 3])
        self.assertEqual([r["capacity"] for r in rows], [1, 2, 3])
        self.assertEqual(prepared.minimum_capacity("lru", 3 / 9), 3)
        self.assertEqual(prepared.minimum_capacity("opt", 3 / 9), 3)

    def test_lru_curve_is_cached(self) -> None:
        prepared = prepare_trace([0, 1, 0, 2, 0, 1])
        a = prepared.lru_curve(backend="python")
        b = prepared.lru_curve(backend="auto")
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()
