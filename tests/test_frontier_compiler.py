from __future__ import annotations

import random
import unittest

from finite_ram_lab.frontier_compiler import (
    TraceState,
    capacity_cliff_ratio,
    compile_frontier,
    potential_dedup_savings,
)


class FrontierCompilerTests(unittest.TestCase):
    def test_empty_trace(self):
        r = compile_frontier([])
        self.assertEqual(r["logical_peak_bytes"], 0)
        self.assertEqual(r["physical_peak_bytes"], 0)

    def test_exact_peak_and_byte_seconds(self):
        states = [
            TraceState("a", 0, 2, logical_bytes=100, encoded_bytes=80),
            TraceState("b", 1, 3, logical_bytes=50, encoded_bytes=60),
        ]
        r = compile_frontier(states)
        self.assertEqual(r["logical_peak_bytes"], 150)
        self.assertEqual(r["physical_peak_bytes"], 140)
        self.assertEqual(r["logical_byte_seconds"], 300.0)
        self.assertEqual(r["physical_byte_seconds"], 280.0)

    def test_physical_overhead_is_visible(self):
        s = TraceState(
            "kv",
            0,
            1,
            logical_bytes=100,
            encoded_bytes=100,
            replicas=2,
            metadata_bytes_per_replica=5,
            fragmentation_bytes=20,
            workspace_bytes=30,
        )
        self.assertEqual(s.physical_bytes, 260)

    def test_release_candidates_fail_closed(self):
        states = [
            TraceState(
                "summary",
                0,
                1,
                logical_bytes=100,
                encoded_bytes=100,
                summary_bytes=10,
                summary_sufficient=True,
            ),
            TraceState(
                "remat",
                0,
                1,
                logical_bytes=100,
                encoded_bytes=100,
                recomputable=True,
            ),
            TraceState(
                "unknown",
                0,
                1,
                logical_bytes=100,
                encoded_bytes=100,
            ),
        ]
        r = compile_frontier(states)
        self.assertEqual(
            r["release_candidates"],
            [
                {"name": "summary", "mode": "REDUCE_AND_RELEASE"},
                {"name": "remat", "mode": "DROP_REMATERIALIZE"},
            ],
        )

    def test_dedup_savings(self):
        s = TraceState(
            "expert",
            0,
            1,
            logical_bytes=1000,
            encoded_bytes=1000,
            replicas=4,
            metadata_bytes_per_replica=10,
        )
        self.assertEqual(potential_dedup_savings(s), 2960)

    def test_capacity_cliff_ratio(self):
        self.assertEqual(capacity_cliff_ratio(900, 1000), 0.9)

    def test_20000_random_sweep_matches_bruteforce_sampled_segments(self):
        rng = random.Random(428)
        for case in range(20_000):
            count = rng.randint(0, 8)
            states = []
            for i in range(count):
                start = rng.randint(0, 8)
                end = rng.randint(start + 1, 10)
                states.append(
                    TraceState(
                        f"s{case}_{i}",
                        start,
                        end,
                        logical_bytes=rng.randint(0, 100),
                        encoded_bytes=rng.randint(0, 100),
                        replicas=rng.randint(1, 3),
                        metadata_bytes_per_replica=rng.randint(0, 5),
                        fragmentation_bytes=rng.randint(0, 10),
                        workspace_bytes=rng.randint(0, 10),
                    )
                )
            r = compile_frontier(states)
            if not states:
                continue
            boundaries = sorted({x for s in states for x in (s.live_start, s.live_end)})
            logical = 0
            physical = 0
            for left, right in zip(boundaries, boundaries[1:]):
                active = [
                    s
                    for s in states
                    if s.live_start <= left and s.live_end >= right
                ]
                logical = max(logical, sum(s.logical_bytes for s in active))
                physical = max(physical, sum(s.physical_bytes for s in active))
            self.assertEqual(r["logical_peak_bytes"], logical)
            self.assertEqual(r["physical_peak_bytes"], physical)


if __name__ == "__main__":
    unittest.main()
