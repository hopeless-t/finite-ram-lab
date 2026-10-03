from __future__ import annotations

import gc
import json
import statistics
import time
from typing import Any

from finite_ram_lab.fr_fp_010_hosted_residency import (
    STATE_MIB,
    STEPS,
    _close_all,
    _fault_state,
    _status_kib,
)

SCHEMA = "finite-ram-lab.fr-fp-011-hosted-rss-calibration/v0.1"

SAFE_FRONTIERS = (2, 4, 6, 8, 10, 12)
STATE_KIB = STATE_MIB * 1024


def _fit_line(
    xs: list[float],
    ys: list[float],
) -> dict[str, float]:
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)

    ss_x = sum(
        (x - x_mean) ** 2
        for x in xs
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
        intercept + slope * x
        for x in xs
    ]

    residuals = [
        y - prediction
        for y, prediction
        in zip(ys, predictions)
    ]

    ss_res = sum(
        residual ** 2
        for residual
        in residuals
    )

    ss_tot = sum(
        (y - y_mean) ** 2
        for y in ys
    )

    r2 = (
        1.0
        if ss_tot == 0.0
        else 1.0 - ss_res / ss_tot
    )

    return {
        "slope": slope,
        "intercept_kib": intercept,
        "r2": r2,
        "max_abs_residual_kib": max(
            abs(value)
            for value in residuals
        ),
    }


def run_frontier(
    safe_frontier: int,
) -> dict[str, Any]:
    if not (
        1
        <= safe_frontier
        <= STEPS
    ):
        raise ValueError(
            "safe_frontier_out_of_range"
        )

    regions = []
    baseline = _status_kib()
    peak_rss = baseline[
        "vmrss_kib"
    ]
    peak_anon = baseline[
        "rssanon_kib"
    ]
    peak_live_states = 0

    try:
        for step in range(
            1,
            STEPS + 1,
        ):
            regions.append(
                _fault_state(step)
            )

            pre_action = _status_kib()

            peak_rss = max(
                peak_rss,
                pre_action[
                    "vmrss_kib"
                ],
            )
            peak_anon = max(
                peak_anon,
                pre_action[
                    "rssanon_kib"
                ],
            )
            peak_live_states = max(
                peak_live_states,
                len(regions),
            )

            if step >= safe_frontier:
                old = regions[:-1]
                current = regions[-1]
                regions = [current]

                for region in old:
                    region.close()

                gc.collect()
                time.sleep(0.005)

        final = _status_kib()

        return {
            "safe_frontier": (
                safe_frontier
            ),
            "logical_peak_kib": (
                safe_frontier
                * STATE_KIB
            ),
            "peak_live_states": (
                peak_live_states
            ),
            "peak_rss_delta_kib": (
                peak_rss
                - baseline[
                    "vmrss_kib"
                ]
            ),
            "peak_rssanon_delta_kib": (
                peak_anon
                - baseline[
                    "rssanon_kib"
                ]
            ),
            "final_rss_delta_kib": (
                final[
                    "vmrss_kib"
                ]
                - baseline[
                    "vmrss_kib"
                ]
            ),
            "final_rssanon_delta_kib": (
                final[
                    "rssanon_kib"
                ]
                - baseline[
                    "rssanon_kib"
                ]
            ),
            "final_live_states": (
                len(regions)
            ),
        }

    finally:
        _close_all(regions)


def run_panel() -> dict[str, Any]:
    rows = [
        run_frontier(
            safe_frontier
        )
        for safe_frontier
        in SAFE_FRONTIERS
    ]

    xs = [
        float(
            row[
                "logical_peak_kib"
            ]
        )
        for row in rows
    ]

    rss = [
        float(
            row[
                "peak_rss_delta_kib"
            ]
        )
        for row in rows
    ]

    anon = [
        float(
            row[
                "peak_rssanon_delta_kib"
            ]
        )
        for row in rows
    ]

    rss_fit = _fit_line(
        xs,
        rss,
    )
    anon_fit = _fit_line(
        xs,
        anon,
    )

    per_state = [
        row[
            "peak_rss_delta_kib"
        ]
        / row[
            "peak_live_states"
        ]
        for row in rows
    ]

    checks = {
        "all_frontiers_match_logical_peak_states": all(
            row[
                "peak_live_states"
            ]
            == row[
                "safe_frontier"
            ]
            for row in rows
        ),
        "all_arms_end_at_one_state": all(
            row[
                "final_live_states"
            ]
            == 1
            for row in rows
        ),
        "rss_fit_is_near_linear": (
            rss_fit[
                "r2"
            ]
            > 0.999
        ),
        "rss_slope_near_one": (
            0.90
            <= rss_fit[
                "slope"
            ]
            <= 1.10
        ),
        "rss_residual_under_4mib": (
            rss_fit[
                "max_abs_residual_kib"
            ]
            < 4096
        ),
        "rssanon_fit_is_near_linear": (
            anon_fit[
                "r2"
            ]
            > 0.999
        ),
        "rssanon_slope_near_one": (
            0.90
            <= anon_fit[
                "slope"
            ]
            <= 1.10
        ),
        "median_physical_kib_per_live_state_near_8mib": (
            0.90
            * STATE_KIB
            <= statistics.median(
                per_state
            )
            <= 1.10
            * STATE_KIB
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
            "HOSTED_LINUX_LIVE_STATE_TO_RSS_CALIBRATION"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "trajectory_steps": (
                STEPS
            ),
            "safe_frontiers": list(
                SAFE_FRONTIERS
            ),
        },
        "rows": rows,
        "rss_fit": rss_fit,
        "rssanon_fit": (
            anon_fit
        ),
        "median_peak_rss_kib_per_live_state": (
            statistics.median(
                per_state
            )
        ),
        "checks": checks,
        "decision": (
            "USE_HOSTED_PHYSICAL_LIVE_STATE_COUNT_AS_A_CALIBRATED_RESIDENT_BYTE_ESTIMATOR_FOR_THIS_MMAP_FIXTURE"
        ),
        "evidence_boundary": (
            "The safe frontiers are synthetic. mmap allocation, page faults, "
            "unmapping, VmRSS and RssAnon calibration are hosted physical."
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_ANONYMOUS_MMAP_LIVE_STATE_RSS_CALIBRATION_ONLY"
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
