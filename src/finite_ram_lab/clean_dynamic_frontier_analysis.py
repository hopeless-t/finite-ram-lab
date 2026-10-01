from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .intrinsic_capacity_clamp import (
    ClampCell,
    classify_cells,
    pressure_classification_accuracy,
    robust_transient_base,
)
from .prelaunch_digital_twin import expected_candidate_frontier


MIB = 1024 * 1024
RELEASE_RE = re.compile(r"^dontneed_(\d+)m$")


@dataclass(frozen=True)
class PlanVector:
    arm: str
    values: tuple[float, ...]


def objective_names(
    spec: dict,
    *,
    include_descriptive: bool = False,
) -> tuple[str, ...]:
    primary = tuple(
        item["name"] for item in spec["frontier_primary_objectives"]
    )
    if not include_descriptive:
        return primary
    descriptive = tuple(
        item["name"] for item in spec["frontier_descriptive_objectives"]
    )
    return primary + descriptive


def pareto_ids(plans: Sequence[PlanVector]) -> tuple[str, ...]:
    out = []
    for i, plan in enumerate(plans):
        dominated = False
        for j, other in enumerate(plans):
            if i == j:
                continue
            if all(x <= y for x, y in zip(other.values, plan.values)) and any(
                x < y for x, y in zip(other.values, plan.values)
            ):
                dominated = True
                break
        if not dominated:
            out.append(plan.arm)
    return tuple(sorted(out))


def _median_cell_plan(
    summary: dict,
    *,
    high: int,
    arm: str,
    names: Sequence[str],
) -> PlanVector:
    cell = summary["cells"][str(high)][arm]
    return PlanVector(
        arm=arm,
        values=tuple(float(cell[f"median_{name}"]) for name in names),
    )


def aggregate_frontier(
    summary: dict,
    spec: dict,
    *,
    high: int,
    include_descriptive: bool = False,
) -> tuple[str, ...]:
    names = objective_names(spec, include_descriptive=include_descriptive)
    plans = [
        _median_cell_plan(summary, high=high, arm=arm, names=names)
        for arm in spec["candidate_arms"]
    ]
    return pareto_ids(plans)


def _block_lookup(summary: dict, high: int, arm: str) -> dict[int, dict]:
    return {
        int(row["block"]): row
        for row in summary["cells"][str(high)][arm]["block_rows"]
    }


def _sampled_frontier(
    summary: dict,
    spec: dict,
    *,
    high: int,
    names: Sequence[str],
    sampled_blocks: Sequence[int],
) -> tuple[str, ...]:
    plans = []
    for arm in spec["candidate_arms"]:
        lookup = _block_lookup(summary, high, arm)
        values = []
        for name in names:
            values.append(
                float(
                    statistics.median(
                        float(lookup[block][name])
                        for block in sampled_blocks
                    )
                )
            )
        plans.append(PlanVector(arm=arm, values=tuple(values)))
    return pareto_ids(plans)


def bootstrap_membership(
    summary: dict,
    spec: dict,
    *,
    high: int,
    include_descriptive: bool,
    iterations: int,
    seed: int,
) -> dict[str, float]:
    if iterations < 1:
        raise ValueError("iterations_invalid")
    names = objective_names(spec, include_descriptive=include_descriptive)
    first_arm = spec["candidate_arms"][0]
    block_ids = tuple(sorted(_block_lookup(summary, high, first_arm)))
    if len(block_ids) < 2:
        raise ValueError("insufficient_blocks")

    # Require identical block IDs across arms.
    for arm in spec["candidate_arms"][1:]:
        if tuple(sorted(_block_lookup(summary, high, arm))) != block_ids:
            raise ValueError("block_identity_mismatch")

    rng = random.Random(seed)
    counts = {arm: 0 for arm in spec["candidate_arms"]}
    for _ in range(iterations):
        sample = tuple(
            block_ids[rng.randrange(len(block_ids))]
            for _ in range(len(block_ids))
        )
        frontier = _sampled_frontier(
            summary,
            spec,
            high=high,
            names=names,
            sampled_blocks=sample,
        )
        for arm in frontier:
            counts[arm] += 1
    return {arm: counts[arm] / iterations for arm in counts}


def bootstrap_transition_loss(
    summary: dict,
    spec: dict,
    *,
    lower_high: int,
    upper_high: int,
    include_descriptive: bool,
    iterations: int,
    seed: int,
) -> dict[str, object]:
    if iterations < 1:
        raise ValueError("iterations_invalid")
    names = objective_names(spec, include_descriptive=include_descriptive)

    first_arm = spec["candidate_arms"][0]
    lower_blocks = tuple(sorted(_block_lookup(summary, lower_high, first_arm)))
    upper_blocks = tuple(sorted(_block_lookup(summary, upper_high, first_arm)))
    rng = random.Random(seed)

    loss_counts = {arm: 0 for arm in spec["candidate_arms"]}
    any_loss = 0
    for _ in range(iterations):
        sample_lower = tuple(
            lower_blocks[rng.randrange(len(lower_blocks))]
            for _ in range(len(lower_blocks))
        )
        sample_upper = tuple(
            upper_blocks[rng.randrange(len(upper_blocks))]
            for _ in range(len(upper_blocks))
        )
        lower_frontier = set(
            _sampled_frontier(
                summary,
                spec,
                high=lower_high,
                names=names,
                sampled_blocks=sample_lower,
            )
        )
        upper_frontier = set(
            _sampled_frontier(
                summary,
                spec,
                high=upper_high,
                names=names,
                sampled_blocks=sample_upper,
            )
        )
        lost = lower_frontier - upper_frontier
        if lost:
            any_loss += 1
        for arm in lost:
            loss_counts[arm] += 1

    return {
        "lower_high": lower_high,
        "upper_high": upper_high,
        "any_loss_probability": any_loss / iterations,
        "arm_loss_probability": {
            arm: loss_counts[arm] / iterations
            for arm in loss_counts
        },
    }


def clamp_replay(summary: dict, spec: dict) -> dict[str, object]:
    cells = []
    clean_floors = []
    for high in spec["memory_high_mib"]:
        for arm in spec["candidate_arms"]:
            match = RELEASE_RE.fullmatch(arm)
            if match is None:
                continue
            release = int(match.group(1))
            cell = summary["cells"][str(high)][arm]
            cells.append(
                ClampCell(
                    memory_high_mib=float(high),
                    release_interval_mib=float(release),
                    peak_mib=float(cell["median_peak_ram_bytes"]) / MIB,
                    memory_high_events=float(
                        cell["median_memory_high_events"]
                    ),
                )
            )
            clean_floors.append(
                float(cell["median_clean_floor_bytes"]) / MIB
            )

    base = robust_transient_base(cells)
    rows = classify_cells(cells, transient_base_mib=base)
    clean_floor_median = float(statistics.median(clean_floors))
    return {
        "transient_base_mib": base,
        "clean_floor_median_mib": clean_floor_median,
        "clean_ephemeral_base_excess_mib": base - clean_floor_median,
        "pressure_classification_accuracy": pressure_classification_accuracy(
            rows
        ),
        "rows": rows,
    }


def analyze_postrun(
    summary: dict,
    spec: dict,
    *,
    bootstrap_iterations: int = 100_000,
    seed: int = 2026100151,
) -> dict[str, object]:
    highs = tuple(int(x) for x in spec["memory_high_mib"])
    threshold = float(spec["qualification"]["frontier_stability_threshold"])

    primary_frontiers = {
        str(high): aggregate_frontier(
            summary,
            spec,
            high=high,
            include_descriptive=False,
        )
        for high in highs
    }
    descriptive_frontiers = {
        str(high): aggregate_frontier(
            summary,
            spec,
            high=high,
            include_descriptive=True,
        )
        for high in highs
    }

    primary_membership = {}
    descriptive_membership = {}
    for index, high in enumerate(highs):
        primary_membership[str(high)] = bootstrap_membership(
            summary,
            spec,
            high=high,
            include_descriptive=False,
            iterations=bootstrap_iterations,
            seed=seed + index * 1000,
        )
        descriptive_membership[str(high)] = bootstrap_membership(
            summary,
            spec,
            high=high,
            include_descriptive=True,
            iterations=bootstrap_iterations,
            seed=seed + 500 + index * 1000,
        )

    primary_transitions = []
    descriptive_transitions = []
    for index, (lower, upper) in enumerate(zip(highs, highs[1:])):
        primary_transitions.append(
            bootstrap_transition_loss(
                summary,
                spec,
                lower_high=lower,
                upper_high=upper,
                include_descriptive=False,
                iterations=bootstrap_iterations,
                seed=seed + 10_000 + index,
            )
        )
        descriptive_transitions.append(
            bootstrap_transition_loss(
                summary,
                spec,
                lower_high=lower,
                upper_high=upper,
                include_descriptive=True,
                iterations=bootstrap_iterations,
                seed=seed + 20_000 + index,
            )
        )

    stable_frontier = {}
    twin_match = {}
    for high in highs:
        aggregate = set(primary_frontiers[str(high)])
        probs = primary_membership[str(high)]
        stable_frontier[str(high)] = all(
            probs[arm] >= threshold for arm in aggregate
        )
        twin_match[str(high)] = tuple(sorted(aggregate)) == tuple(
            sorted(expected_candidate_frontier(high))
        )

    primary_aggregate_losses = []
    descriptive_aggregate_losses = []
    for lower, upper in zip(highs, highs[1:]):
        primary_aggregate_losses.append(
            tuple(
                sorted(
                    set(primary_frontiers[str(lower)])
                    - set(primary_frontiers[str(upper)])
                )
            )
        )
        descriptive_aggregate_losses.append(
            tuple(
                sorted(
                    set(descriptive_frontiers[str(lower)])
                    - set(descriptive_frontiers[str(upper)])
                )
            )
        )

    if (
        not any(primary_aggregate_losses)
        and any(descriptive_aggregate_losses)
    ):
        projection_classification = "PROJECTION_FRAGILE"
    elif any(primary_aggregate_losses):
        projection_classification = "PRIMARY_TRANSITION_PRESENT"
    else:
        projection_classification = "NO_AGGREGATE_FRONTIER_LOSS"

    return {
        "primary_frontiers": primary_frontiers,
        "descriptive_frontiers": descriptive_frontiers,
        "primary_membership_probability": primary_membership,
        "descriptive_membership_probability": descriptive_membership,
        "primary_transition_bootstrap": primary_transitions,
        "descriptive_transition_bootstrap": descriptive_transitions,
        "stable_primary_frontier_by_capacity": stable_frontier,
        "prelaunch_twin_match_by_capacity": twin_match,
        "primary_aggregate_losses": primary_aggregate_losses,
        "descriptive_aggregate_losses": descriptive_aggregate_losses,
        "projection_classification": projection_classification,
        "clamp_replay": clamp_replay(summary, spec),
        "bootstrap_iterations": bootstrap_iterations,
        "seed": seed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=2026100151)
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    result = analyze_postrun(
        summary,
        spec,
        bootstrap_iterations=args.iterations,
        seed=args.seed,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
