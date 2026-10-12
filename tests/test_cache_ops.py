from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.cache_ops import (
    analyze_trace,
    benchmark_trace,
    load_trace_json,
    parse_capacities,
    synthetic_trace,
)


class CacheOpsTests(unittest.TestCase):
    def test_parse_capacities(self) -> None:
        self.assertEqual(parse_capacities("3,7,7,17"), [3, 7, 17])

    def test_json_trace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "trace.json"
            path.write_text('["a", "b", "a", "c"]')
            self.assertEqual(load_trace_json(path), ["a", "b", "a", "c"])

    def test_analyze_and_benchmark(self) -> None:
        trace = synthetic_trace(
            family="shifting_hotset",
            seed=10,
            length=500,
            universe=31,
            capacity_anchor=7,
        )
        analysis = analyze_trace(trace, capacities=[3, 7, 17])
        self.assertEqual(analysis["lru_curve_points"], len(set(trace)))
        bench = benchmark_trace(
            trace,
            capacities=[3, 7, 17],
            anchor_capacity=7,
            repeats=2,
        )
        self.assertEqual(bench["parity"]["status"], "PASS")
        self.assertGreater(bench["speedups"]["anchor_pair"], 0)


if __name__ == "__main__":
    unittest.main()
