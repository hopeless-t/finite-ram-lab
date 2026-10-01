from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import json
from math import gcd
from pathlib import Path
import random
from typing import Sequence


Matrix = tuple[tuple[int, ...], ...]


class FidelityClass(str, Enum):
    EXACT = "EXACT"
    BOUNDED_ERROR = "BOUNDED_ERROR"
    EMPIRICAL_CAPABILITY = "EMPIRICAL_CAPABILITY"


@dataclass(frozen=True)
class RepresentationContract:
    domain: str
    obligation: str
    resident_representation: str
    fidelity_class: FidelityClass
    proof_or_gate: str


@dataclass(frozen=True)
class CRTResidencyResult:
    strategy: str
    rows: int
    cols: int
    inner: int
    lane_count: int
    moduli: tuple[int, ...]
    modulus_product: int
    conservative_abs_bound: int
    logical_peak_intermediate_bytes: int
    exact_match: bool
    output: Matrix


@dataclass(frozen=True)
class CRTComparison:
    all_resident: CRTResidencyResult
    streamed: CRTResidencyResult
    peak_reduction_bytes: int
    peak_reduction_fraction: float


DEFAULT_MODULI = (127, 125, 121, 119, 113, 109, 107)


def _matrix(value: Sequence[Sequence[int]]) -> Matrix:
    rows = tuple(tuple(int(item) for item in row) for row in value)
    if not rows or not rows[0]:
        raise ValueError("matrix_empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix_ragged")
    return rows


def _validate_gemm(a: Matrix, b: Matrix) -> tuple[int, int, int]:
    rows = len(a)
    inner = len(a[0])
    if len(b) != inner:
        raise ValueError("gemm_inner_mismatch")
    cols = len(b[0])
    return rows, cols, inner


def _validate_moduli(moduli: Sequence[int]) -> tuple[int, ...]:
    values = tuple(int(item) for item in moduli)
    if not values:
        raise ValueError("moduli_empty")
    if any(item <= 1 for item in values):
        raise ValueError("modulus_invalid")
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            if gcd(left, right) != 1:
                raise ValueError("moduli_not_pairwise_coprime")
    return values


def integer_gemm(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]]) -> Matrix:
    left = _matrix(a)
    right = _matrix(b)
    rows, cols, inner = _validate_gemm(left, right)
    return tuple(
        tuple(
            sum(left[row][axis] * right[axis][col] for axis in range(inner))
            for col in range(cols)
        )
        for row in range(rows)
    )


def gemm_conservative_abs_bound(
    a: Sequence[Sequence[int]],
    b: Sequence[Sequence[int]],
) -> int:
    left = _matrix(a)
    right = _matrix(b)
    rows, cols, inner = _validate_gemm(left, right)
    return max(
        sum(abs(left[row][axis]) * abs(right[axis][col]) for axis in range(inner))
        for row in range(rows)
        for col in range(cols)
    )


def residue_gemm(a: Matrix, b: Matrix, modulus: int) -> Matrix:
    rows, cols, inner = _validate_gemm(a, b)
    return tuple(
        tuple(
            sum(
                (a[row][axis] % modulus) * (b[axis][col] % modulus)
                for axis in range(inner)
            )
            % modulus
            for col in range(cols)
        )
        for row in range(rows)
    )


def _unsigned_bytes_for_modulus(modulus: int) -> int:
    return max(1, ((modulus - 1).bit_length() + 7) // 8)


def _crt_update_matrix(
    state: Matrix,
    state_modulus: int,
    residue: Matrix,
    modulus: int,
) -> tuple[Matrix, int]:
    inverse = pow(state_modulus % modulus, -1, modulus)
    rows = len(state)
    cols = len(state[0])
    next_state = tuple(
        tuple(
            state[row][col]
            + state_modulus
            * (((residue[row][col] - state[row][col]) * inverse) % modulus)
            for col in range(cols)
        )
        for row in range(rows)
    )
    return next_state, state_modulus * modulus


def _center_matrix(state: Matrix, modulus_product: int) -> Matrix:
    half = modulus_product // 2
    return tuple(
        tuple(value - modulus_product if value > half else value for value in row)
        for row in state
    )


def _zero_state(rows: int, cols: int) -> Matrix:
    return tuple(tuple(0 for _ in range(cols)) for _ in range(rows))


def _require_uniqueness(moduli: tuple[int, ...], bound: int) -> int:
    product = 1
    for modulus in moduli:
        product *= modulus
    if product <= 2 * bound:
        raise ValueError("crt_uniqueness_not_proven")
    return product


def all_resident_crt_gemm(
    a: Sequence[Sequence[int]],
    b: Sequence[Sequence[int]],
    moduli: Sequence[int],
) -> CRTResidencyResult:
    left = _matrix(a)
    right = _matrix(b)
    rows, cols, inner = _validate_gemm(left, right)
    mods = _validate_moduli(moduli)
    bound = gemm_conservative_abs_bound(left, right)
    product = _require_uniqueness(mods, bound)
    element_count = rows * cols

    residue_lanes: list[Matrix] = []
    lane_resident_bytes = 0
    peak = 0
    for modulus in mods:
        lane = residue_gemm(left, right, modulus)
        residue_lanes.append(lane)
        lane_resident_bytes += element_count * _unsigned_bytes_for_modulus(modulus)
        peak = max(peak, lane_resident_bytes)

    state = _zero_state(rows, cols)
    state_modulus = 1
    for lane, modulus in zip(residue_lanes, mods, strict=True):
        state, state_modulus = _crt_update_matrix(state, state_modulus, lane, modulus)
        accumulator_bytes = element_count * _unsigned_bytes_for_modulus(state_modulus)
        peak = max(peak, lane_resident_bytes + accumulator_bytes)

    output = _center_matrix(state, state_modulus)
    exact = output == integer_gemm(left, right)
    return CRTResidencyResult(
        strategy="ALL_RESIDENT",
        rows=rows,
        cols=cols,
        inner=inner,
        lane_count=len(mods),
        moduli=mods,
        modulus_product=product,
        conservative_abs_bound=bound,
        logical_peak_intermediate_bytes=peak,
        exact_match=exact,
        output=output,
    )


def streamed_crt_gemm(
    a: Sequence[Sequence[int]],
    b: Sequence[Sequence[int]],
    moduli: Sequence[int],
) -> CRTResidencyResult:
    left = _matrix(a)
    right = _matrix(b)
    rows, cols, inner = _validate_gemm(left, right)
    mods = _validate_moduli(moduli)
    bound = gemm_conservative_abs_bound(left, right)
    product = _require_uniqueness(mods, bound)
    element_count = rows * cols

    state = _zero_state(rows, cols)
    state_modulus = 1
    peak = 0

    for modulus in mods:
        lane = residue_gemm(left, right, modulus)
        lane_bytes = element_count * _unsigned_bytes_for_modulus(modulus)
        next_state, next_modulus = _crt_update_matrix(
            state,
            state_modulus,
            lane,
            modulus,
        )
        accumulator_bytes = element_count * _unsigned_bytes_for_modulus(next_modulus)
        peak = max(peak, lane_bytes + accumulator_bytes)
        state = next_state
        state_modulus = next_modulus
        del lane

    output = _center_matrix(state, state_modulus)
    exact = output == integer_gemm(left, right)
    return CRTResidencyResult(
        strategy="STREAMED_FOLD",
        rows=rows,
        cols=cols,
        inner=inner,
        lane_count=len(mods),
        moduli=mods,
        modulus_product=product,
        conservative_abs_bound=bound,
        logical_peak_intermediate_bytes=peak,
        exact_match=exact,
        output=output,
    )


def compare_crt_residency(
    a: Sequence[Sequence[int]],
    b: Sequence[Sequence[int]],
    moduli: Sequence[int],
) -> CRTComparison:
    all_resident = all_resident_crt_gemm(a, b, moduli)
    streamed = streamed_crt_gemm(a, b, moduli)
    if not all_resident.exact_match or not streamed.exact_match:
        raise AssertionError("exact_gemm_mismatch")
    if all_resident.output != streamed.output:
        raise AssertionError("strategy_output_mismatch")
    reduction = (
        all_resident.logical_peak_intermediate_bytes
        - streamed.logical_peak_intermediate_bytes
    )
    fraction = (
        reduction / all_resident.logical_peak_intermediate_bytes
        if all_resident.logical_peak_intermediate_bytes
        else 0.0
    )
    return CRTComparison(
        all_resident=all_resident,
        streamed=streamed,
        peak_reduction_bytes=reduction,
        peak_reduction_fraction=fraction,
    )


def unified_contracts() -> tuple[RepresentationContract, ...]:
    return (
        RepresentationContract(
            domain="ozaki_crt",
            obligation="exact wide integer result",
            resident_representation="one residue lane plus future-sufficient CRT fold state",
            fidelity_class=FidelityClass.EXACT,
            proof_or_gate="pairwise-coprime residues and modulus product > 2*conservative bound",
        ),
        RepresentationContract(
            domain="ternary_model",
            obligation="task capability under a frozen evaluation contract",
            resident_representation="packed ternary weights plus scales and runtime state",
            fidelity_class=FidelityClass.EMPIRICAL_CAPABILITY,
            proof_or_gate="held-out task quality and runtime identity; no bit-exact equivalence claim",
        ),
        RepresentationContract(
            domain="kitten_review",
            obligation="review coverage and semantic fidelity",
            resident_representation="bounded microshard plus overlap plus accumulated evidence",
            fidelity_class=FidelityClass.EMPIRICAL_CAPABILITY,
            proof_or_gate="coverage, semantic-drift, rare-miss, and strong-review acceptance",
        ),
    )


def _random_matrix(rng: random.Random, rows: int, cols: int, limit: int) -> Matrix:
    return tuple(
        tuple(rng.randint(-limit, limit) for _ in range(cols))
        for _ in range(rows)
    )


def software_panel(seed: int = 461, size: int = 32) -> dict[str, object]:
    rng = random.Random(seed)
    a = _random_matrix(rng, size, size, 8)
    b = _random_matrix(rng, size, size, 8)
    rows = []
    for lane_count in range(2, len(DEFAULT_MODULI) + 1):
        comparison = compare_crt_residency(a, b, DEFAULT_MODULI[:lane_count])
        rows.append(
            {
                "lane_count": lane_count,
                "moduli": list(DEFAULT_MODULI[:lane_count]),
                "modulus_product": comparison.streamed.modulus_product,
                "conservative_abs_bound": comparison.streamed.conservative_abs_bound,
                "all_resident_peak_bytes": comparison.all_resident.logical_peak_intermediate_bytes,
                "streamed_peak_bytes": comparison.streamed.logical_peak_intermediate_bytes,
                "peak_reduction_bytes": comparison.peak_reduction_bytes,
                "peak_reduction_fraction": comparison.peak_reduction_fraction,
                "exact_match": comparison.streamed.exact_match,
            }
        )
    return {
        "schema": "finite-ram-lab.obligation-residency-panel/v0.1",
        "claim_ceiling": "SOFTWARE_EXACT_LOGICAL_RESIDENCY_ONLY",
        "seed": seed,
        "matrix_size": size,
        "fidelity_contracts": [
            {**asdict(item), "fidelity_class": item.fidelity_class.value}
            for item in unified_contracts()
        ],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=461)
    parser.add_argument("--size", type=int, default=32)
    args = parser.parse_args()
    payload = software_panel(seed=args.seed, size=args.size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
