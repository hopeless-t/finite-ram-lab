from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class Choice:
    choice_id: str
    objective_vector: tuple[float, ...]
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.choice_id:
            raise ValueError("choice_id_empty")
        if not self.objective_vector:
            raise ValueError("objective_vector_empty")
        if any(not isfinite(float(value)) for value in self.objective_vector):
            raise ValueError("objective_nonfinite")
        if not self.provenance:
            object.__setattr__(self, "provenance", (self.choice_id,))
        elif any(not value for value in self.provenance):
            raise ValueError("provenance_invalid")


@dataclass(frozen=True)
class GlobalPlan:
    choice_ids: tuple[str, ...]
    objective_vector: tuple[float, ...]
    provenance_groups: tuple[tuple[str, ...], ...]


def dominates(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    if len(left) != len(right):
        raise ValueError("objective_dimension_mismatch")
    return all(x <= y for x, y in zip(left, right)) and any(
        x < y for x, y in zip(left, right)
    )


def pareto_group(choices: Sequence[Choice]) -> tuple[Choice, ...]:
    if not choices:
        raise ValueError("choice_group_empty")
    width = len(choices[0].objective_vector)
    if any(len(choice.objective_vector) != width for choice in choices):
        raise ValueError("objective_dimension_mismatch")

    out = []
    for i, choice in enumerate(choices):
        if any(
            j != i
            and dominates(other.objective_vector, choice.objective_vector)
            for j, other in enumerate(choices)
        ):
            continue
        out.append(choice)
    return tuple(
        sorted(out, key=lambda item: (item.objective_vector, item.choice_id))
    )


def quotient_group(choices: Sequence[Choice]) -> tuple[Choice, ...]:
    """Prune locally dominated choices and collapse exact objective-vector ties.

    Provenance of tied physical choices is retained on the canonical member.
    """
    frontier = pareto_group(choices)
    by_vector: dict[tuple[float, ...], list[Choice]] = {}
    for choice in frontier:
        by_vector.setdefault(choice.objective_vector, []).append(choice)

    out = []
    for vector, tied in by_vector.items():
        canonical = min(tied, key=lambda item: item.choice_id)
        provenance = tuple(
            sorted(
                {
                    source
                    for item in tied
                    for source in item.provenance
                }
            )
        )
        out.append(
            Choice(
                choice_id=canonical.choice_id,
                objective_vector=vector,
                provenance=provenance,
            )
        )

    return tuple(
        sorted(out, key=lambda item: (item.objective_vector, item.choice_id))
    )


def combination_count(groups: Sequence[Sequence[Choice]]) -> int:
    total = 1
    for group in groups:
        if not group:
            raise ValueError("choice_group_empty")
        total *= len(group)
    return total


def enumerate_global_plans(
    groups: Sequence[Sequence[Choice]],
) -> tuple[GlobalPlan, ...]:
    if not groups:
        return ()
    width = len(groups[0][0].objective_vector)
    for group in groups:
        if not group:
            raise ValueError("choice_group_empty")
        if any(len(choice.objective_vector) != width for choice in group):
            raise ValueError("objective_dimension_mismatch")

    plans = []
    for selection in product(*groups):
        vector = tuple(
            sum(choice.objective_vector[index] for choice in selection)
            for index in range(width)
        )
        plans.append(
            GlobalPlan(
                choice_ids=tuple(choice.choice_id for choice in selection),
                objective_vector=vector,
                provenance_groups=tuple(
                    choice.provenance for choice in selection
                ),
            )
        )
    return tuple(plans)


def global_pareto_vectors(
    groups: Sequence[Sequence[Choice]],
) -> tuple[tuple[float, ...], ...]:
    plans = enumerate_global_plans(groups)
    vectors = tuple(sorted({plan.objective_vector for plan in plans}))
    out = []
    for i, vector in enumerate(vectors):
        if any(
            j != i and dominates(other, vector)
            for j, other in enumerate(vectors)
        ):
            continue
        out.append(vector)
    return tuple(out)


def quotient_groups(
    groups: Sequence[Sequence[Choice]],
) -> tuple[tuple[Choice, ...], ...]:
    return tuple(quotient_group(group) for group in groups)


def quotient_statistics(
    groups: Sequence[Sequence[Choice]],
) -> dict[str, object]:
    compiled = quotient_groups(groups)
    raw = combination_count(groups)
    reduced = combination_count(compiled)
    return {
        "raw_group_sizes": tuple(len(group) for group in groups),
        "quotient_group_sizes": tuple(len(group) for group in compiled),
        "raw_combination_count": raw,
        "quotient_combination_count": reduced,
        "combination_reduction_fraction": 1.0 - reduced / raw,
    }
