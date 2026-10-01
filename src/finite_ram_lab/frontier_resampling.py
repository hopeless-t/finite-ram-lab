from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from random import Random
from statistics import median
from typing import Mapping, Sequence

from finite_ram_lab.historical_dynamic_replay import (
    ProjectedObservation,
    projected_frontier,
)


@dataclass(frozen=True)
class BootstrapResult:
    iterations: int
    target_plan_id: str
    loss_probability: float
    small_membership_probability: float
    large_membership_probability: float
    loss_count: int
    small_member_count: int
    large_member_count: int


def _aggregate_blocks(
    blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    sample: Sequence[str],
    objective_names: Sequence[str],
) -> tuple[ProjectedObservation, ...]:
    if not sample:
        raise ValueError("sample_empty")

    arms = sorted(next(iter(blocks.values())).keys())
    observations = []

    for arm in arms:
        objectives = []
        for objective in objective_names:
            values = [
                float(blocks[block][arm][objective])
                for block in sample
            ]
            objectives.append((objective, float(median(values))))
        observations.append(
            ProjectedObservation(
                plan_id=arm,
                objectives=tuple(objectives),
            )
        )

    return tuple(observations)


def leave_one_block_out_frontiers(
    blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    objective_names: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    keys = tuple(sorted(blocks))
    if len(keys) < 2:
        raise ValueError("need_at_least_two_blocks")

    out = {}
    for omitted in keys:
        sample = tuple(block for block in keys if block != omitted)
        frontier = projected_frontier(
            _aggregate_blocks(blocks, sample, objective_names),
            objective_names,
        )
        out[omitted] = tuple(sorted(plan.plan_id for plan in frontier))
    return out


def bootstrap_frontier_loss(
    smaller_blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    larger_blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    objective_names: Sequence[str],
    *,
    target_plan_id: str,
    iterations: int,
    seed: int,
) -> BootstrapResult:
    if type(iterations) is not int or iterations < 1:
        raise ValueError("iterations_invalid")
    if not target_plan_id:
        raise ValueError("target_plan_id_empty")

    small_keys = tuple(sorted(smaller_blocks))
    large_keys = tuple(sorted(larger_blocks))
    if not small_keys or not large_keys:
        raise ValueError("blocks_empty")

    rng = Random(seed)
    loss = small_member = large_member = 0

    for _ in range(iterations):
        small_sample = tuple(
            small_keys[rng.randrange(len(small_keys))]
            for _ in range(len(small_keys))
        )
        large_sample = tuple(
            large_keys[rng.randrange(len(large_keys))]
            for _ in range(len(large_keys))
        )

        small_frontier = {
            p.plan_id
            for p in projected_frontier(
                _aggregate_blocks(
                    smaller_blocks,
                    small_sample,
                    objective_names,
                ),
                objective_names,
            )
        }
        large_frontier = {
            p.plan_id
            for p in projected_frontier(
                _aggregate_blocks(
                    larger_blocks,
                    large_sample,
                    objective_names,
                ),
                objective_names,
            )
        }

        in_small = target_plan_id in small_frontier
        in_large = target_plan_id in large_frontier
        small_member += int(in_small)
        large_member += int(in_large)
        loss += int(in_small and not in_large)

    return BootstrapResult(
        iterations=iterations,
        target_plan_id=target_plan_id,
        loss_probability=loss / iterations,
        small_membership_probability=small_member / iterations,
        large_membership_probability=large_member / iterations,
        loss_count=loss,
        small_member_count=small_member,
        large_member_count=large_member,
    )


def bootstrap_any_frontier_loss(
    smaller_blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    larger_blocks: Mapping[str, Mapping[str, Mapping[str, float]]],
    objective_names: Sequence[str],
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | int]:
    if type(iterations) is not int or iterations < 1:
        raise ValueError("iterations_invalid")

    small_keys = tuple(sorted(smaller_blocks))
    large_keys = tuple(sorted(larger_blocks))
    rng = Random(seed)
    any_loss = 0
    loss_sizes = Counter()

    for _ in range(iterations):
        small_sample = tuple(
            small_keys[rng.randrange(len(small_keys))]
            for _ in range(len(small_keys))
        )
        large_sample = tuple(
            large_keys[rng.randrange(len(large_keys))]
            for _ in range(len(large_keys))
        )

        small_frontier = {
            p.plan_id
            for p in projected_frontier(
                _aggregate_blocks(
                    smaller_blocks,
                    small_sample,
                    objective_names,
                ),
                objective_names,
            )
        }
        large_frontier = {
            p.plan_id
            for p in projected_frontier(
                _aggregate_blocks(
                    larger_blocks,
                    large_sample,
                    objective_names,
                ),
                objective_names,
            )
        }

        lost = small_frontier - large_frontier
        any_loss += int(bool(lost))
        loss_sizes[len(lost)] += 1

    return {
        "iterations": iterations,
        "any_loss_probability": any_loss / iterations,
        "no_loss_probability": 1.0 - any_loss / iterations,
        "loss_size_0_count": loss_sizes[0],
        "loss_size_1plus_count": iterations - loss_sizes[0],
    }
