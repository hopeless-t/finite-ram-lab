from __future__ import annotations

import argparse
import json
from fractions import Fraction
from typing import Any

MIB = 1024 * 1024
SCHEMA = "finite-ram-lab.fr-p9-012-horizon-price-policy-regions/v0.1"
MODES = ("KEEP_WARM", "FAULT_IN")

# Frozen median anchors from FR-P9-011 hosted physical artifact
# sha256:4ac83d72124f3982d8cebb860d04e54628d75dc8356f7cd703baf7fce5113b59
ANCHORS: dict[int, dict[str, dict[str, int]]] = {
    1: {
        "KEEP_WARM": {"memory_peak_bytes": 128_284_672, "materialize_ns_total": 50_635_663},
        "FAULT_IN": {"memory_peak_bytes": 99_876_864, "materialize_ns_total": 75_274_834},
    },
    2: {
        "KEEP_WARM": {"memory_peak_bytes": 136_527_872, "materialize_ns_total": 51_645_035},
        "FAULT_IN": {"memory_peak_bytes": 103_159_808, "materialize_ns_total": 101_839_837},
    },
    4: {
        "KEEP_WARM": {"memory_peak_bytes": 136_912_896, "materialize_ns_total": 52_099_568},
        "FAULT_IN": {"memory_peak_bytes": 103_417_856, "materialize_ns_total": 201_856_215},
    },
    8: {
        "KEEP_WARM": {"memory_peak_bytes": 136_488_960, "materialize_ns_total": 52_182_239},
        "FAULT_IN": {"memory_peak_bytes": 103_004_160, "materialize_ns_total": 413_431_851},
    },
}


def _validate_anchor(anchor: dict[str, dict[str, int]]) -> None:
    if set(anchor) != set(MODES):
        raise ValueError("anchor_modes_must_be_keep_warm_and_fault_in")
    warm = anchor["KEEP_WARM"]
    fault = anchor["FAULT_IN"]
    for mode, row in anchor.items():
        if int(row["memory_peak_bytes"]) <= 0 or int(row["materialize_ns_total"]) < 0:
            raise ValueError(f"invalid_anchor:{mode}")
    if int(fault["memory_peak_bytes"]) >= int(warm["memory_peak_bytes"]):
        raise ValueError("expected_fault_in_lower_peak")
    if int(fault["materialize_ns_total"]) <= int(warm["materialize_ns_total"]):
        raise ValueError("expected_fault_in_higher_materialize_cost")


def break_even_price_ns_per_mib(anchor: dict[str, dict[str, int]]) -> Fraction:
    """External RAM price where KEEP_WARM and FAULT_IN have equal priced cost.

    Price units are nanoseconds per MiB of peak memory. The conversion is
    explicit and external; the lab does not invent the price.
    """
    _validate_anchor(anchor)
    warm = anchor["KEEP_WARM"]
    fault = anchor["FAULT_IN"]
    delta_latency = int(fault["materialize_ns_total"]) - int(warm["materialize_ns_total"])
    delta_bytes = int(warm["memory_peak_bytes"]) - int(fault["memory_peak_bytes"])
    return Fraction(delta_latency * MIB, delta_bytes)


def _coerce_price(value: int | float | Fraction | None) -> Fraction | None:
    if value is None:
        return None
    price = value if isinstance(value, Fraction) else Fraction(str(value))
    if price < 0:
        raise ValueError("external_memory_price_must_be_nonnegative")
    return price


def _feasible_modes(
    anchor: dict[str, dict[str, int]],
    *,
    capacity_bytes: int,
    max_materialize_ns: int | None,
) -> list[str]:
    if capacity_bytes < 0:
        raise ValueError("capacity_bytes_must_be_nonnegative")
    if max_materialize_ns is not None and max_materialize_ns < 0:
        raise ValueError("max_materialize_ns_must_be_nonnegative")
    feasible: list[str] = []
    for mode in MODES:
        row = anchor[mode]
        if int(row["memory_peak_bytes"]) > capacity_bytes:
            continue
        if max_materialize_ns is not None and int(row["materialize_ns_total"]) > max_materialize_ns:
            continue
        feasible.append(mode)
    return feasible


def direct_policy(
    anchor: dict[str, dict[str, int]],
    *,
    capacity_bytes: int,
    external_memory_price_ns_per_mib: int | float | Fraction | None,
    max_materialize_ns: int | None = None,
) -> str:
    """Direct solver: hard feasibility first, optional external price second."""
    _validate_anchor(anchor)
    price = _coerce_price(external_memory_price_ns_per_mib)
    feasible = _feasible_modes(
        anchor,
        capacity_bytes=capacity_bytes,
        max_materialize_ns=max_materialize_ns,
    )
    if not feasible:
        return "NO_FEASIBLE_POLICY"
    if len(feasible) == 1:
        return feasible[0]
    if price is None:
        return "TYPED_FRONTIER_UNRESOLVED"

    costs: dict[str, Fraction] = {}
    for mode in feasible:
        row = anchor[mode]
        costs[mode] = Fraction(int(row["materialize_ns_total"]), 1) + (
            price * Fraction(int(row["memory_peak_bytes"]), MIB)
        )
    warm_cost = costs["KEEP_WARM"]
    fault_cost = costs["FAULT_IN"]
    if warm_cost < fault_cost:
        return "KEEP_WARM"
    if fault_cost < warm_cost:
        return "FAULT_IN"
    return "PRICE_TIE"


def compiled_policy(
    anchor: dict[str, dict[str, int]],
    *,
    capacity_bytes: int,
    external_memory_price_ns_per_mib: int | float | Fraction | None,
    max_materialize_ns: int | None = None,
) -> str:
    """Compiled boundary lookup specialized for the qualified P9-011 shape."""
    _validate_anchor(anchor)
    price = _coerce_price(external_memory_price_ns_per_mib)
    warm = anchor["KEEP_WARM"]
    fault = anchor["FAULT_IN"]
    fault_peak = int(fault["memory_peak_bytes"])
    warm_peak = int(warm["memory_peak_bytes"])
    warm_latency = int(warm["materialize_ns_total"])
    fault_latency = int(fault["materialize_ns_total"])

    if capacity_bytes < 0:
        raise ValueError("capacity_bytes_must_be_nonnegative")
    if max_materialize_ns is not None and max_materialize_ns < 0:
        raise ValueError("max_materialize_ns_must_be_nonnegative")

    if capacity_bytes < fault_peak:
        return "NO_FEASIBLE_POLICY"

    if capacity_bytes < warm_peak:
        if max_materialize_ns is not None and max_materialize_ns < fault_latency:
            return "NO_FEASIBLE_POLICY"
        return "FAULT_IN"

    if max_materialize_ns is not None:
        if max_materialize_ns < warm_latency:
            return "NO_FEASIBLE_POLICY"
        if max_materialize_ns < fault_latency:
            return "KEEP_WARM"

    if price is None:
        return "TYPED_FRONTIER_UNRESOLVED"
    threshold = break_even_price_ns_per_mib(anchor)
    if price < threshold:
        return "KEEP_WARM"
    if price > threshold:
        return "FAULT_IN"
    return "PRICE_TIE"


def compile_regions(anchor: dict[str, dict[str, int]]) -> dict[str, Any]:
    _validate_anchor(anchor)
    warm = anchor["KEEP_WARM"]
    fault = anchor["FAULT_IN"]
    threshold = break_even_price_ns_per_mib(anchor)
    return {
        "fault_in_peak_bytes": int(fault["memory_peak_bytes"]),
        "keep_warm_peak_bytes": int(warm["memory_peak_bytes"]),
        "keep_warm_materialize_ns": int(warm["materialize_ns_total"]),
        "fault_in_materialize_ns": int(fault["materialize_ns_total"]),
        "break_even_price_ns_per_mib": float(threshold),
        "break_even_price_ms_per_mib": float(threshold) / 1_000_000.0,
        "regions": [
            "capacity < FAULT_IN peak => NO_FEASIBLE_POLICY",
            "FAULT_IN peak <= capacity < KEEP_WARM peak => FAULT_IN iff latency SLO admits it",
            "capacity >= KEEP_WARM peak and latency SLO < KEEP_WARM latency => NO_FEASIBLE_POLICY",
            "capacity >= KEEP_WARM peak and KEEP_WARM latency <= SLO < FAULT_IN latency => KEEP_WARM",
            "capacity >= KEEP_WARM peak and both latency-feasible => external price below/tie/above break-even selects KEEP_WARM/TIE/FAULT_IN",
        ],
    }


def _verification_grid(anchor: dict[str, dict[str, int]]) -> list[tuple[int, Fraction | None, int | None]]:
    warm = anchor["KEEP_WARM"]
    fault = anchor["FAULT_IN"]
    fp = int(fault["memory_peak_bytes"])
    kp = int(warm["memory_peak_bytes"])
    kl = int(warm["materialize_ns_total"])
    fl = int(fault["materialize_ns_total"])
    threshold = break_even_price_ns_per_mib(anchor)
    capacities = sorted({0, max(0, fp - 1), fp, (fp + kp) // 2, max(fp, kp - 1), kp, kp + MIB})
    prices: list[Fraction | None] = [
        None,
        Fraction(0, 1),
        threshold / 2,
        max(Fraction(0, 1), threshold - Fraction(1, 1)),
        threshold,
        threshold + Fraction(1, 1),
        threshold * 2,
    ]
    slos = [None, 0, max(0, kl - 1), kl, (kl + fl) // 2, fl, fl + 1]
    return [(c, p, s) for c in capacities for p in prices for s in slos]


def run_panel() -> dict[str, Any]:
    regions: dict[str, Any] = {}
    mismatches: list[dict[str, Any]] = []
    comparisons = 0
    thresholds: list[tuple[int, float]] = []

    for horizon, anchor in sorted(ANCHORS.items()):
        compiled = compile_regions(anchor)
        regions[str(horizon)] = compiled
        thresholds.append((horizon, float(compiled["break_even_price_ns_per_mib"])))
        for capacity, price, slo in _verification_grid(anchor):
            direct = direct_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=price,
                max_materialize_ns=slo,
            )
            lookup = compiled_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=price,
                max_materialize_ns=slo,
            )
            comparisons += 1
            if direct != lookup:
                mismatches.append(
                    {
                        "horizon": horizon,
                        "capacity_bytes": capacity,
                        "price": None if price is None else float(price),
                        "max_materialize_ns": slo,
                        "direct": direct,
                        "compiled": lookup,
                    }
                )

    threshold_monotone = all(b > a for (_, a), (_, b) in zip(thresholds, thresholds[1:]))
    checks = {
        "compiled_lookup_matches_direct_solver": not mismatches,
        "verification_grid_is_nontrivial": comparisons >= 1000,
        "break_even_price_rises_with_reuse_horizon": threshold_monotone,
        "no_external_price_leaves_both_feasible_policies_unresolved": all(
            direct_policy(
                anchor,
                capacity_bytes=max(
                    int(anchor["KEEP_WARM"]["memory_peak_bytes"]),
                    int(anchor["FAULT_IN"]["memory_peak_bytes"]),
                ),
                external_memory_price_ns_per_mib=None,
                max_materialize_ns=None,
            ) == "TYPED_FRONTIER_UNRESOLVED"
            for anchor in ANCHORS.values()
        ),
        "capacity_feasibility_precedes_scalar_price": all(
            direct_policy(
                anchor,
                capacity_bytes=int(anchor["FAULT_IN"]["memory_peak_bytes"]),
                external_memory_price_ns_per_mib=0,
                max_materialize_ns=None,
            ) == "FAULT_IN"
            for anchor in ANCHORS.values()
        ),
        "policy_compiler_does_not_grant_authority": True,
        "policy_compiler_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "ANALYTIC_COMPILATION_OVER_HOSTED_FR_P9_011_ANCHORS",
        "source_evidence": {
            "pr": 203,
            "experiment": "FR-P9-011",
            "artifact_sha256": "4ac83d72124f3982d8cebb860d04e54628d75dc8356f7cd703baf7fce5113b59",
            "anchor_statistic": "median_of_two_hosted_repetitions_per_mode_and_horizon",
        },
        "policy_regions": regions,
        "verification": {"comparisons": comparisons, "mismatches": mismatches},
        "checks": checks,
        "decision": (
            "COMPILE_RESIDENCY_POLICY_FROM_EXTERNAL_CONSTRAINTS_AND_PRICES;"
            "CAPACITY_AND_LATENCY_FEASIBILITY_PRECEDE_PRICE;"
            "REUSE_HORIZON_SHIFTS_THE_BREAK_EVEN_RAM_PRICE;"
            "NO_EXTERNAL_PRICE_MEANS_NO_SCALAR_WINNER"
        ),
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "next_falsifier": (
            "validate the compiled horizon/price regions against a different physical workload shape "
            "and test whether the policy-boundary ordering survives without reusing the hashing proxy"
        ),
        "claim_ceiling": (
            "ANALYTIC_POLICY_BOUNDARY_COMPILATION_OVER_HOSTED_FR_P9_011_MEDIAN_ANCHORS_ONLY_"
            "NO_UNIVERSAL_MEMORY_PRICE_OR_APPLICATION_POLICY_CLAIM"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    result = run_panel()
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
