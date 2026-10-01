from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence


@dataclass(frozen=True)
class CadenceClass:
    advice_calls: int
    representative_cadence_mib: int
    mechanism_only_cadences_mib: tuple[int, ...]
    activation_threshold_mib: float


def advice_calls(*, file_span_mib: float, cadence_mib: int) -> int:
    if file_span_mib <= 0:
        raise ValueError("file_span_invalid")
    if type(cadence_mib) is not int or cadence_mib <= 0:
        raise ValueError("cadence_invalid")
    return int(ceil(file_span_mib / cadence_mib))


def compile_cadence_classes(
    *,
    file_span_mib: float,
    cadences_mib: Sequence[int],
    transient_base_mib: float,
) -> tuple[CadenceClass, ...]:
    if transient_base_mib < 0:
        raise ValueError("transient_base_invalid")
    if not cadences_mib:
        raise ValueError("cadences_empty")
    if any(type(k) is not int or k <= 0 for k in cadences_mib):
        raise ValueError("cadence_invalid")
    if len(set(cadences_mib)) != len(cadences_mib):
        raise ValueError("cadence_duplicate")

    grouped: dict[int, list[int]] = {}
    for cadence in sorted(cadences_mib):
        grouped.setdefault(
            advice_calls(
                file_span_mib=file_span_mib,
                cadence_mib=cadence,
            ),
            [],
        ).append(cadence)

    classes = []
    for calls, members in grouped.items():
        representative = min(members)
        mechanism_only = tuple(k for k in members if k != representative)
        classes.append(
            CadenceClass(
                advice_calls=calls,
                representative_cadence_mib=representative,
                mechanism_only_cadences_mib=mechanism_only,
                activation_threshold_mib=transient_base_mib + representative,
            )
        )

    return tuple(
        sorted(
            classes,
            key=lambda item: item.representative_cadence_mib,
        )
    )


def symbolic_frontier(
    *,
    memory_high_mib: float,
    classes: Sequence[CadenceClass],
) -> tuple[int, ...]:
    if memory_high_mib <= 0:
        raise ValueError("memory_high_invalid")
    if not classes:
        raise ValueError("classes_empty")

    fallback = max(
        classes,
        key=lambda item: item.representative_cadence_mib,
    ).representative_cadence_mib

    active = {
        item.representative_cadence_mib
        for item in classes
        if memory_high_mib >= item.activation_threshold_mib
    }
    active.add(fallback)
    return tuple(sorted(active))


def topology_regimes(
    classes: Sequence[CadenceClass],
) -> tuple[dict[str, object], ...]:
    if not classes:
        raise ValueError("classes_empty")

    ordered = tuple(
        sorted(classes, key=lambda item: item.representative_cadence_mib)
    )
    fallback = ordered[-1].representative_cadence_mib
    thresholds = sorted(
        {
            item.activation_threshold_mib
            for item in ordered
            if item.representative_cadence_mib != fallback
        }
    )

    regimes = []
    lower = None
    for threshold in thresholds:
        probe = threshold - 1e-9
        regimes.append(
            {
                "lower_inclusive_mib": lower,
                "upper_exclusive_mib": threshold,
                "frontier_cadences_mib": symbolic_frontier(
                    memory_high_mib=max(probe, 1e-9),
                    classes=ordered,
                ),
            }
        )
        lower = threshold

    probe = (thresholds[-1] if thresholds else 0.0) + 1e-9
    regimes.append(
        {
            "lower_inclusive_mib": lower,
            "upper_exclusive_mib": None,
            "frontier_cadences_mib": symbolic_frontier(
                memory_high_mib=max(probe, 1e-9),
                classes=ordered,
            ),
        }
    )
    return tuple(regimes)


def brute_frontier(
    *,
    file_span_mib: float,
    cadences_mib: Sequence[int],
    transient_base_mib: float,
    clean_floor_mib: float,
    memory_high_mib: float,
) -> tuple[int, ...]:
    if memory_high_mib < clean_floor_mib:
        raise ValueError("capacity_below_clean_floor")

    plans = []
    for cadence in cadences_mib:
        intrinsic = transient_base_mib + cadence
        peak = min(intrinsic, memory_high_mib)
        pressure = int(intrinsic > memory_high_mib)
        plans.append(
            (
                cadence,
                (
                    peak,
                    peak - clean_floor_mib,
                    float(pressure),
                    float(pressure),
                    float(
                        advice_calls(
                            file_span_mib=file_span_mib,
                            cadence_mib=cadence,
                        )
                    ),
                ),
            )
        )

    frontier = []
    for i, (cadence, vector) in enumerate(plans):
        dominated = False
        for j, (_, other) in enumerate(plans):
            if i == j:
                continue
            if all(x <= y for x, y in zip(other, vector)) and any(
                x < y for x, y in zip(other, vector)
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(cadence)

    return tuple(sorted(frontier))


def compilation_summary(
    *,
    file_span_mib: float,
    cadences_mib: Sequence[int],
    transient_base_mib: float,
) -> dict[str, object]:
    classes = compile_cadence_classes(
        file_span_mib=file_span_mib,
        cadences_mib=cadences_mib,
        transient_base_mib=transient_base_mib,
    )
    representatives = tuple(
        item.representative_cadence_mib for item in classes
    )
    mechanism_only = tuple(
        sorted(
            cadence
            for item in classes
            for cadence in item.mechanism_only_cadences_mib
        )
    )
    return {
        "candidate_count": len(cadences_mib),
        "representative_count": len(representatives),
        "search_reduction_fraction": 1.0 - len(representatives) / len(cadences_mib),
        "representatives_mib": representatives,
        "mechanism_only_mib": mechanism_only,
        "classes": classes,
        "regimes": topology_regimes(classes),
    }
