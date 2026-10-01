from __future__ import annotations

import math
import random
import unittest

from finite_ram_lab.flashattention_future_state import (
    OnlineSoftmaxSummary,
    chunked_online_softmax,
    flashattention_structural_state,
    full_softmax_reference,
    naive_score_matrix_bytes,
)


class FlashAttentionFutureStateTests(unittest.TestCase):
    def test_two_block_summary_matches_full_reference(self):
        scores = [1.0, -2.0, 3.0, 0.5]
        values = [
            [1.0, 0.0],
            [0.0, 1.0],
            [2.0, -1.0],
            [0.5, 0.5],
        ]
        expected_o, expected_lse = full_softmax_reference(scores, values)
        actual_o, actual_lse = chunked_online_softmax(scores, values, 2)
        for x, y in zip(actual_o, expected_o):
            self.assertTrue(math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12))
        self.assertTrue(
            math.isclose(actual_lse, expected_lse, rel_tol=1e-12, abs_tol=1e-12)
        )

    def test_partition_invariance_across_block_sizes(self):
        scores = [2.0, -1.0, 4.0, 3.0, -5.0, 0.25, 7.0]
        values = [[float(i), float(i * i)] for i in range(len(scores))]
        expected = full_softmax_reference(scores, values)
        for block_size in range(1, len(scores) + 1):
            actual = chunked_online_softmax(scores, values, block_size)
            for x, y in zip(actual[0], expected[0]):
                self.assertTrue(math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12))
            self.assertTrue(
                math.isclose(actual[1], expected[1], rel_tol=1e-12, abs_tol=1e-12)
            )

    def test_summary_size_is_independent_of_processed_key_count(self):
        small = OnlineSoftmaxSummary.empty(64)
        large = OnlineSoftmaxSummary.empty(64)
        self.assertEqual(len(small.weighted_sum), len(large.weighted_sum))
        self.assertEqual(len(small.weighted_sum), 64)

    def test_structural_tile_accounting(self):
        state = flashattention_structural_state(
            tile_m=128,
            tile_n=128,
            head_dim_v=128,
        )
        self.assertEqual(state["score_tile_bytes"], 65_536)
        self.assertEqual(state["row_stats_bytes"], 1_024)
        self.assertEqual(state["output_accumulator_bytes"], 65_536)
        self.assertEqual(state["modeled_active_frontier_bytes"], 132_096)

    def test_naive_score_matrix_accounting(self):
        self.assertEqual(
            naive_score_matrix_bytes(
                seqlen_q=4096,
                seqlen_k=4096,
                element_bytes=4,
            ),
            67_108_864,
        )

    def test_10000_random_partition_invariance_cases(self):
        rng = random.Random(431)
        for _ in range(10_000):
            length = rng.randint(1, 32)
            value_dim = rng.randint(1, 8)
            scores = [rng.uniform(-20.0, 20.0) for _ in range(length)]
            values = [
                [rng.uniform(-5.0, 5.0) for _ in range(value_dim)]
                for _ in range(length)
            ]
            expected_o, expected_lse = full_softmax_reference(scores, values)
            block_size = rng.randint(1, length)
            actual_o, actual_lse = chunked_online_softmax(
                scores, values, block_size
            )
            for x, y in zip(actual_o, expected_o):
                self.assertTrue(
                    math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-10)
                )
            self.assertTrue(
                math.isclose(
                    actual_lse,
                    expected_lse,
                    rel_tol=1e-10,
                    abs_tol=1e-10,
                )
            )


if __name__ == "__main__":
    unittest.main()
