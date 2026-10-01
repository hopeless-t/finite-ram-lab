from __future__ import annotations

from dataclasses import dataclass
from math import exp, inf, log
from typing import Iterable, Sequence


@dataclass(frozen=True)
class OnlineSoftmaxSummary:
    row_max: float
    row_sum: float
    weighted_sum: tuple[float, ...]

    @staticmethod
    def empty(value_dim: int) -> "OnlineSoftmaxSummary":
        if type(value_dim) is not int or value_dim < 1:
            raise ValueError("value_dim_invalid")
        return OnlineSoftmaxSummary(-inf, 0.0, (0.0,) * value_dim)

    def update(
        self,
        scores: Sequence[float],
        values: Sequence[Sequence[float]],
    ) -> "OnlineSoftmaxSummary":
        if not scores:
            return self
        if len(scores) != len(values):
            raise ValueError("score_value_length_mismatch")
        value_dim = len(self.weighted_sum)
        if any(len(v) != value_dim for v in values):
            raise ValueError("value_dim_mismatch")

        block_max = max(float(s) for s in scores)
        new_max = max(self.row_max, block_max)
        old_scale = 0.0 if self.row_max == -inf else exp(self.row_max - new_max)

        weights = [exp(float(s) - new_max) for s in scores]
        new_sum = self.row_sum * old_scale + sum(weights)

        accum = [x * old_scale for x in self.weighted_sum]
        for w, value in zip(weights, values):
            for j, x in enumerate(value):
                accum[j] += w * float(x)

        return OnlineSoftmaxSummary(new_max, new_sum, tuple(accum))

    def finalize(self) -> tuple[tuple[float, ...], float]:
        if self.row_sum <= 0.0:
            raise ValueError("empty_or_invalid_summary")
        output = tuple(x / self.row_sum for x in self.weighted_sum)
        lse = self.row_max + log(self.row_sum)
        return output, lse


def full_softmax_reference(
    scores: Sequence[float],
    values: Sequence[Sequence[float]],
) -> tuple[tuple[float, ...], float]:
    if not scores:
        raise ValueError("scores_empty")
    if len(scores) != len(values):
        raise ValueError("score_value_length_mismatch")
    value_dim = len(values[0])
    if value_dim < 1 or any(len(v) != value_dim for v in values):
        raise ValueError("value_dim_mismatch")

    row_max = max(float(s) for s in scores)
    weights = [exp(float(s) - row_max) for s in scores]
    denom = sum(weights)
    output = []
    for j in range(value_dim):
        output.append(
            sum(w * float(v[j]) for w, v in zip(weights, values)) / denom
        )
    return tuple(output), row_max + log(denom)


def chunked_online_softmax(
    scores: Sequence[float],
    values: Sequence[Sequence[float]],
    block_size: int,
) -> tuple[tuple[float, ...], float]:
    if type(block_size) is not int or block_size < 1:
        raise ValueError("block_size_invalid")
    if not values:
        raise ValueError("values_empty")
    summary = OnlineSoftmaxSummary.empty(len(values[0]))
    for start in range(0, len(scores), block_size):
        summary = summary.update(
            scores[start : start + block_size],
            values[start : start + block_size],
        )
    return summary.finalize()


def flashattention_structural_state(
    *,
    tile_m: int,
    tile_n: int,
    head_dim_v: int,
    score_accum_bytes: int = 4,
    output_accum_bytes: int = 4,
    stat_bytes: int = 4,
) -> dict[str, int]:
    for name, value in (
        ("tile_m", tile_m),
        ("tile_n", tile_n),
        ("head_dim_v", head_dim_v),
        ("score_accum_bytes", score_accum_bytes),
        ("output_accum_bytes", output_accum_bytes),
        ("stat_bytes", stat_bytes),
    ):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name}_invalid")

    score_tile = tile_m * tile_n * score_accum_bytes
    row_stats = tile_m * 2 * stat_bytes
    output_accum = tile_m * head_dim_v * output_accum_bytes
    return {
        "score_tile_bytes": score_tile,
        "row_stats_bytes": row_stats,
        "output_accumulator_bytes": output_accum,
        "future_sufficient_summary_bytes": row_stats + output_accum,
        "modeled_active_frontier_bytes": score_tile + row_stats + output_accum,
    }


def naive_score_matrix_bytes(
    *,
    seqlen_q: int,
    seqlen_k: int,
    element_bytes: int,
) -> int:
    for name, value in (
        ("seqlen_q", seqlen_q),
        ("seqlen_k", seqlen_k),
        ("element_bytes", element_bytes),
    ):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name}_invalid")
    return seqlen_q * seqlen_k * element_bytes
