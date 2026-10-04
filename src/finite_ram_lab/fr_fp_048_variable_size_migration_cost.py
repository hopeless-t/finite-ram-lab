from __future__ import annotations

import json
import math
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _size_bytes,
)
from finite_ram_lab.fr_fp_047_hosted_variable_size_budget import (
    _enforce_tier_sized,
)

SCHEMA = "finite-ram-lab.fr-fp-048-variable-size-migration-cost/v0.1"

STATE_SIZES_MIB = (
    4,
    6,
    8,
    10,
    12,
    14,
    16,
)
REPEATS = 3


def _fit_affine(
    xs: list[float],
    ys: list[float],
) -> dict[str, float]:
    x_mean = statistics.fmean(
        xs
    )
    y_mean = statistics.fmean(
        ys
    )
    ss_x = sum(
        (x - x_mean) ** 2
        for x in xs
    )

    if ss_x <= 0.0:
        raise ValueError(
            "affine_fit_requires_multiple_sizes"
        )

    slope = (
        sum(
            (x - x_mean)
            * (y - y_mean)
            for x, y
            in zip(xs, ys)
        )
        / ss_x
    )
    intercept = (
        y_mean
        - slope * x_mean
    )
    predictions = [
        intercept
        + slope * x
        for x in xs
    ]
    residuals = [
        y - predicted
        for y, predicted
        in zip(
            ys,
            predictions,
        )
    ]
    ss_res = sum(
        value ** 2
        for value in residuals
    )
    ss_tot = sum(
        (y - y_mean) ** 2
        for y in ys
    )

    return {
        "intercept_ms": intercept,
        "slope_ms_per_mib": (
            slope
        ),
        "r2": (
            1.0
            if ss_tot <= 0.0
            else (
                1.0
                - ss_res / ss_tot
            )
        ),
        "mae_ms": statistics.fmean(
            abs(value)
            for value in residuals
        ),
        "max_abs_residual_ms": max(
            abs(value)
            for value in residuals
        ),
    }


def _loo_mae(
    rows: list[dict[str, Any]],
    *,
    model: str,
) -> float:
    errors = []
    sizes = sorted(
        {
            int(
                row[
                    "state_mib"
                ]
            )
            for row in rows
        }
    )

    for held_size in sizes:
        training = [
            row
            for row in rows
            if row[
                "state_mib"
            ]
            != held_size
        ]
        held = [
            row
            for row in rows
            if row[
                "state_mib"
            ]
            == held_size
        ]

        if model == "CONSTANT_PER_ACTION":
            prediction = (
                statistics.fmean(
                    row[
                        "elapsed_ms"
                    ]
                    for row
                    in training
                )
            )
        elif model == "AFFINE_BYTES":
            fit = _fit_affine(
                [
                    float(
                        row[
                            "state_mib"
                        ]
                    )
                    for row
                    in training
                ],
                [
                    float(
                        row[
                            "elapsed_ms"
                        ]
                    )
                    for row
                    in training
                ],
            )
            prediction = (
                fit[
                    "intercept_ms"
                ]
                + fit[
                    "slope_ms_per_mib"
                ]
                * held_size
            )
        else:
            raise ValueError(
                f"unknown_model:{model}"
            )

        errors.extend(
            abs(
                float(
                    row[
                        "elapsed_ms"
                    ]
                )
                - prediction
            )
            for row in held
        )

    return statistics.fmean(
        errors
    )


def _summarize_direction(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    xs = [
        float(
            row[
                "state_mib"
            ]
        )
        for row in rows
    ]
    ys = [
        float(
            row[
                "elapsed_ms"
            ]
        )
        for row in rows
    ]
    affine = _fit_affine(
        xs,
        ys,
    )
    constant_loo = _loo_mae(
        rows,
        model=(
            "CONSTANT_PER_ACTION"
        ),
    )
    affine_loo = _loo_mae(
        rows,
        model=(
            "AFFINE_BYTES"
        ),
    )

    preferred = (
        "AFFINE_BYTES"
        if affine_loo
        < constant_loo
        else "CONSTANT_PER_ACTION"
    )

    by_size = {}

    for size in STATE_SIZES_MIB:
        selected = [
            row[
                "elapsed_ms"
            ]
            for row in rows
            if row[
                "state_mib"
            ]
            == size
        ]
        by_size[
            str(size)
        ] = {
            "count": len(
                selected
            ),
            "median_ms": (
                statistics.median(
                    selected
                )
            ),
            "mean_ms": (
                statistics.fmean(
                    selected
                )
            ),
            "min_ms": min(
                selected
            ),
            "max_ms": max(
                selected
            ),
        }

    return {
        "count": len(rows),
        "affine_fit": affine,
        "constant_loo_mae_ms": (
            constant_loo
        ),
        "affine_loo_mae_ms": (
            affine_loo
        ),
        "affine_relative_loo_improvement": (
            1.0
            - affine_loo
            / constant_loo
            if constant_loo
            > 0.0
            else 0.0
        ),
        "preferred_by_lower_loo_mae": (
            preferred
        ),
        "by_size": by_size,
    }


def run_panel() -> dict[str, Any]:
    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-048-"
    ) as tmp:
        root = Path(tmp)

        for size_index, size_mib in enumerate(
            STATE_SIZES_MIB
        ):
            path = root / (
                f"state-{size_mib}mib.bin"
            )
            size_bytes = _size_bytes(
                size_mib
            )
            prepared = _prepare_tier(
                path,
                size_bytes=size_bytes,
                marker=(
                    210
                    + size_index
                ),
                cold=True,
            )

            if not prepared[
                "verified"
            ]:
                raise RuntimeError(
                    f"prepare_failed:{size_mib}"
                )

            try:
                for repeat in range(
                    1,
                    REPEATS + 1,
                ):
                    cold_before = (
                        _file_residency(
                            path
                        )[
                            "resident_fraction"
                        ]
                    )

                    started = (
                        time.monotonic_ns()
                    )
                    promoted = (
                        _enforce_tier_sized(
                            path,
                            tier="WARM",
                            size_bytes=(
                                size_bytes
                            ),
                        )
                    )
                    promote_ns = (
                        time.monotonic_ns()
                        - started
                    )

                    rows.append(
                        {
                            "direction": (
                                "PROMOTE"
                            ),
                            "state_mib": (
                                size_mib
                            ),
                            "repeat": repeat,
                            "elapsed_ns": (
                                promote_ns
                            ),
                            "elapsed_ms": (
                                promote_ns
                                / 1_000_000.0
                            ),
                            "pre_resident_fraction": (
                                cold_before
                            ),
                            "post_resident_fraction": (
                                promoted[
                                    "resident_fraction"
                                ]
                            ),
                            "prefetch_bytes": (
                                promoted[
                                    "prefetch_bytes"
                                ]
                            ),
                        }
                    )

                    warm_before = (
                        _file_residency(
                            path
                        )[
                            "resident_fraction"
                        ]
                    )

                    started = (
                        time.monotonic_ns()
                    )
                    evicted = (
                        _enforce_tier_sized(
                            path,
                            tier="COLD",
                            size_bytes=(
                                size_bytes
                            ),
                        )
                    )
                    evict_ns = (
                        time.monotonic_ns()
                        - started
                    )

                    rows.append(
                        {
                            "direction": (
                                "EVICT"
                            ),
                            "state_mib": (
                                size_mib
                            ),
                            "repeat": repeat,
                            "elapsed_ns": (
                                evict_ns
                            ),
                            "elapsed_ms": (
                                evict_ns
                                / 1_000_000.0
                            ),
                            "pre_resident_fraction": (
                                warm_before
                            ),
                            "post_resident_fraction": (
                                evicted[
                                    "resident_fraction"
                                ]
                            ),
                            "prefetch_bytes": 0,
                        }
                    )

            finally:
                try:
                    _fadvise_dontneed(
                        path
                    )
                except Exception:
                    pass

                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    promote = [
        row
        for row in rows
        if row[
            "direction"
        ]
        == "PROMOTE"
    ]
    evict = [
        row
        for row in rows
        if row[
            "direction"
        ]
        == "EVICT"
    ]

    promote_summary = (
        _summarize_direction(
            promote
        )
    )
    evict_summary = (
        _summarize_direction(
            evict
        )
    )

    checks = {
        "all_sizes_have_three_promote_and_three_evict_measurements": all(
            sum(
                row[
                    "direction"
                ]
                == "PROMOTE"
                and row[
                    "state_mib"
                ]
                == size
                for row in rows
            )
            == REPEATS
            and sum(
                row[
                    "direction"
                ]
                == "EVICT"
                and row[
                    "state_mib"
                ]
                == size
                for row in rows
            )
            == REPEATS
            for size in (
                STATE_SIZES_MIB
            )
        ),
        "every_promote_starts_cold": all(
            row[
                "pre_resident_fraction"
            ]
            <= 0.10
            for row in promote
        ),
        "every_promote_ends_warm": all(
            row[
                "post_resident_fraction"
            ]
            >= 0.95
            for row in promote
        ),
        "every_promote_prefetches_exact_state_bytes": all(
            row[
                "prefetch_bytes"
            ]
            == _size_bytes(
                int(
                    row[
                        "state_mib"
                    ]
                )
            )
            for row in promote
        ),
        "every_evict_starts_warm": all(
            row[
                "pre_resident_fraction"
            ]
            >= 0.95
            for row in evict
        ),
        "every_evict_ends_cold": all(
            row[
                "post_resident_fraction"
            ]
            <= 0.10
            for row in evict
        ),
        "all_timings_are_positive": all(
            row[
                "elapsed_ns"
            ]
            > 0
            for row in rows
        ),
        "both_model_families_cross_validate": all(
            math.isfinite(
                summary[
                    key
                ]
            )
            for summary in (
                promote_summary,
                evict_summary,
            )
            for key in (
                "constant_loo_mae_ms",
                "affine_loo_mae_ms",
            )
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "HOSTED_PHYSICAL_VARIABLE_SIZE_DIRECTIONAL_MIGRATION_COST_CALIBRATION"
        ),
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "repeats_per_size": (
                REPEATS
            ),
            "physical_action_count": (
                len(rows)
            ),
        },
        "promote": (
            promote_summary
        ),
        "evict": (
            evict_summary
        ),
        "rows": rows,
        "checks": checks,
        "decision": (
            "SELECT_DIRECTIONAL_MIGRATION_COST_MODEL_BY_HELD_OUT_SIZE_ERROR_NOT_BY_EQUAL_SIZE_ASSUMPTION"
        ),
        "evidence_boundary": (
            "Wall time includes the qualified actuator's intentional settle sleeps; "
            "the model describes this actuator contract, not raw kernel I/O alone."
        ),
        "next": (
            "USE_THE_SELECTED_DIRECTIONAL_BYTE_COST_MODEL_IN_VARIABLE_SIZE_MIGRATION_HYSTERESIS"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_DIRECTIONAL_MIGRATION_COST_ON_SEVEN_STATE_SIZES_AND_THREE_REPEATS_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
