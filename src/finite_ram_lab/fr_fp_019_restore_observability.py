from __future__ import annotations

import json
import math
import random
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_012_hosted_cold_spill import (
    _memory_current_bytes,
    _self_cgroup_dir,
)
from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _restore,
    _size_bytes,
)

SCHEMA = "finite-ram-lab.fr-fp-019-restore-observability/v0.1"

STATE_MIB = 8
BLOCKS = 32
PRE_WINDOW_MS = 20
PERMUTATIONS = 10_000
SEED = 20261004
ARMS = (
    "WARM_PAGECACHE",
    "COLD_DONTNEED",
)
PRE_FEATURES = (
    "global_io_some_pre_delta_us",
    "global_io_full_pre_delta_us",
    "cgroup_io_some_pre_delta_us",
    "cgroup_rbytes_pre_delta",
    "memory_current_pre_delta_bytes",
)
BONFERRONI_ALPHA = (
    0.05
    / len(
        PRE_FEATURES
    )
)


def _psi(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "available": False,
            "some_total_us": None,
            "full_total_us": None,
        }

    out: dict[str, Any] = {
        "available": True,
        "some_total_us": None,
        "full_total_us": None,
    }

    try:
        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        out[
            "available"
        ] = False
        return out

    for line in lines:
        parts = line.split()

        if not parts:
            continue

        kind = parts[0]

        if kind not in {
            "some",
            "full",
        }:
            continue

        fields = {}

        for item in parts[
            1:
        ]:
            if "=" not in item:
                continue
            key, value = item.split(
                "=",
                1,
            )
            fields[key] = value

        if "total" in fields:
            try:
                out[
                    kind
                    + "_total_us"
                ] = int(
                    fields[
                        "total"
                    ]
                )
            except ValueError:
                pass

    return out


def _io_stat() -> dict[str, Any]:
    directory = _self_cgroup_dir()

    if directory is None:
        return {
            "available": False,
            "rbytes": None,
            "wbytes": None,
            "rios": None,
            "wios": None,
        }

    path = (
        directory
        / "io.stat"
    )

    if not path.exists():
        return {
            "available": False,
            "rbytes": None,
            "wbytes": None,
            "rios": None,
            "wios": None,
        }

    totals = {
        "rbytes": 0,
        "wbytes": 0,
        "rios": 0,
        "wios": 0,
    }

    try:
        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return {
            "available": False,
            **{
                key: None
                for key in totals
            },
        }

    for line in lines:
        parts = line.split()

        for item in parts[
            1:
        ]:
            if "=" not in item:
                continue

            key, value = item.split(
                "=",
                1,
            )

            if key in totals:
                try:
                    totals[key] += int(
                        value
                    )
                except ValueError:
                    pass

    return {
        "available": True,
        **totals,
    }


def _load1() -> float | None:
    path = Path(
        "/proc/loadavg"
    )

    if not path.exists():
        return None

    try:
        return float(
            path.read_text(
                encoding="utf-8"
            ).split()[0]
        )
    except (
        OSError,
        ValueError,
        IndexError,
    ):
        return None


def _snapshot() -> dict[str, Any]:
    directory = _self_cgroup_dir()
    cgroup_psi_path = (
        None
        if directory is None
        else (
            directory
            / "io.pressure"
        )
    )

    return {
        "time_ns": (
            time.monotonic_ns()
        ),
        "global_io_psi": (
            _psi(
                Path(
                    "/proc/pressure/io"
                )
            )
        ),
        "cgroup_io_psi": (
            _psi(
                cgroup_psi_path
            )
            if cgroup_psi_path
            is not None
            else {
                "available": False,
                "some_total_us": None,
                "full_total_us": None,
            }
        ),
        "io_stat": (
            _io_stat()
        ),
        "memory_current_bytes": (
            _memory_current_bytes()
        ),
        "load1": (
            _load1()
        ),
    }


def _delta(
    before: int | None,
    after: int | None,
) -> int | None:
    if (
        before is None
        or after is None
    ):
        return None

    return (
        after - before
    )


def _feature_row(
    before: dict[str, Any],
    after: dict[str, Any],
    prefix: str,
) -> dict[str, Any]:
    return {
        (
            "global_io_some_"
            + prefix
            + "_delta_us"
        ): _delta(
            before[
                "global_io_psi"
            ][
                "some_total_us"
            ],
            after[
                "global_io_psi"
            ][
                "some_total_us"
            ],
        ),
        (
            "global_io_full_"
            + prefix
            + "_delta_us"
        ): _delta(
            before[
                "global_io_psi"
            ][
                "full_total_us"
            ],
            after[
                "global_io_psi"
            ][
                "full_total_us"
            ],
        ),
        (
            "cgroup_io_some_"
            + prefix
            + "_delta_us"
        ): _delta(
            before[
                "cgroup_io_psi"
            ][
                "some_total_us"
            ],
            after[
                "cgroup_io_psi"
            ][
                "some_total_us"
            ],
        ),
        (
            "cgroup_io_full_"
            + prefix
            + "_delta_us"
        ): _delta(
            before[
                "cgroup_io_psi"
            ][
                "full_total_us"
            ],
            after[
                "cgroup_io_psi"
            ][
                "full_total_us"
            ],
        ),
        (
            "cgroup_rbytes_"
            + prefix
            + "_delta"
        ): _delta(
            before[
                "io_stat"
            ][
                "rbytes"
            ],
            after[
                "io_stat"
            ][
                "rbytes"
            ],
        ),
        (
            "cgroup_wbytes_"
            + prefix
            + "_delta"
        ): _delta(
            before[
                "io_stat"
            ][
                "wbytes"
            ],
            after[
                "io_stat"
            ][
                "wbytes"
            ],
        ),
        (
            "memory_current_"
            + prefix
            + "_delta_bytes"
        ): _delta(
            before[
                "memory_current_bytes"
            ],
            after[
                "memory_current_bytes"
            ],
        ),
    }


def _ranks(
    values: list[float],
) -> list[float]:
    order = sorted(
        range(
            len(values)
        ),
        key=lambda index: (
            values[index]
        ),
    )
    ranks = [
        0.0
        for _ in values
    ]
    position = 0

    while position < len(
        order
    ):
        end = position + 1

        while (
            end
            < len(order)
            and values[
                order[end]
            ]
            == values[
                order[
                    position
                ]
            ]
        ):
            end += 1

        average_rank = (
            (
                position + 1
                + end
            )
            / 2.0
        )

        for cursor in range(
            position,
            end,
        ):
            ranks[
                order[cursor]
            ] = average_rank

        position = end

    return ranks


def _pearson(
    left: list[float],
    right: list[float],
) -> float | None:
    left_mean = (
        statistics.fmean(
            left
        )
    )
    right_mean = (
        statistics.fmean(
            right
        )
    )

    numerator = sum(
        (a - left_mean)
        * (b - right_mean)
        for a, b
        in zip(
            left,
            right,
        )
    )
    left_ss = sum(
        (a - left_mean) ** 2
        for a in left
    )
    right_ss = sum(
        (b - right_mean) ** 2
        for b in right
    )

    if (
        left_ss <= 0.0
        or right_ss <= 0.0
    ):
        return None

    return (
        numerator
        / math.sqrt(
            left_ss
            * right_ss
        )
    )


def _spearman(
    left: list[float],
    right: list[float],
) -> float | None:
    if (
        len(left)
        != len(right)
        or len(left) < 3
    ):
        return None

    return _pearson(
        _ranks(left),
        _ranks(right),
    )


def _permutation_p(
    feature: list[float],
    latency: list[float],
    *,
    seed: int,
) -> dict[str, Any]:
    observed = _spearman(
        feature,
        latency,
    )

    if observed is None:
        return {
            "rho": None,
            "p_abs": None,
        }

    rng = random.Random(
        seed
    )
    extreme = 0

    for _ in range(
        PERMUTATIONS
    ):
        shuffled = list(
            latency
        )
        rng.shuffle(
            shuffled
        )
        rho = _spearman(
            feature,
            shuffled,
        )

        if (
            rho is not None
            and abs(rho)
            >= abs(observed)
        ):
            extreme += 1

    return {
        "rho": observed,
        "p_abs": (
            1 + extreme
        ) / (
            PERMUTATIONS + 1
        ),
    }


def _trial(
    root: Path,
    *,
    block: int,
    arm: str,
) -> dict[str, Any]:
    size_bytes = _size_bytes(
        STATE_MIB
    )
    marker = (
        block * 3
        + (
            1
            if arm
            == "WARM_PAGECACHE"
            else 2
        )
    )
    path = root / (
        f"b{block:03d}-"
        + arm.lower()
        + ".bin"
    )

    prepared = _prepare_tier(
        path,
        size_bytes=size_bytes,
        marker=marker,
        cold=(
            arm
            == "COLD_DONTNEED"
        ),
    )
    residency = (
        _file_residency(
            path
        )
    )

    pre0 = _snapshot()
    time.sleep(
        PRE_WINDOW_MS
        / 1000.0
    )
    pre1 = _snapshot()

    restored = _restore(
        path,
        size_bytes=size_bytes,
        marker=marker,
    )
    post = _snapshot()

    features = {
        **_feature_row(
            pre0,
            pre1,
            "pre",
        ),
        **_feature_row(
            pre1,
            post,
            "restore",
        ),
    }

    row = {
        "block": block,
        "arm": arm,
        "prepare_verified": (
            prepared[
                "verified"
            ]
        ),
        "restore_verified": (
            restored[
                "verified"
            ]
        ),
        "pre_resident_fraction": (
            residency[
                "resident_fraction"
            ]
        ),
        "read_ns": (
            restored[
                "read_ns"
            ]
        ),
        "load1_pre": (
            pre1[
                "load1"
            ]
        ),
        "global_psi_available": (
            pre1[
                "global_io_psi"
            ][
                "available"
            ]
        ),
        "cgroup_psi_available": (
            pre1[
                "cgroup_io_psi"
            ][
                "available"
            ]
        ),
        "cgroup_io_stat_available": (
            pre1[
                "io_stat"
            ][
                "available"
            ]
        ),
        "memory_current_available": (
            pre1[
                "memory_current_bytes"
            ]
            is not None
        ),
        **features,
    }

    _fadvise_dontneed(
        path
    )
    path.unlink()
    time.sleep(
        0.002
    )

    return row


def _median_ms(
    rows: list[
        dict[str, Any]
    ],
) -> float:
    return statistics.median(
        row[
            "read_ns"
        ]
        / 1_000_000.0
        for row in rows
    )


def _analyze_pre_features(
    cold: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    latency = [
        row[
            "read_ns"
        ]
        / 1_000_000.0
        for row in cold
    ]
    results = {}

    for index, feature in enumerate(
        PRE_FEATURES
    ):
        pairs = [
            (
                row[
                    feature
                ],
                latency_value,
            )
            for row, latency_value
            in zip(
                cold,
                latency,
            )
            if row[
                feature
            ]
            is not None
        ]

        if len(pairs) < 8:
            results[
                feature
            ] = {
                "rho": None,
                "p_abs": None,
                "n": len(
                    pairs
                ),
            }
            continue

        values = [
            float(pair[0])
            for pair in pairs
        ]
        latencies = [
            float(pair[1])
            for pair in pairs
        ]

        result = _permutation_p(
            values,
            latencies,
            seed=(
                SEED
                + index
            ),
        )
        results[
            feature
        ] = {
            **result,
            "n": len(
                pairs
            ),
        }

    significant = [
        feature
        for feature, result
        in results.items()
        if (
            result[
                "p_abs"
            ]
            is not None
            and result[
                "p_abs"
            ]
            <= BONFERRONI_ALPHA
        )
    ]

    return {
        "features": results,
        "bonferroni_alpha": (
            BONFERRONI_ALPHA
        ),
        "significant_features": (
            significant
        ),
    }


def _diagnostic_correlations(
    cold: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    latency = [
        row[
            "read_ns"
        ]
        / 1_000_000.0
        for row in cold
    ]
    out = {}

    for feature in (
        "global_io_some_restore_delta_us",
        "global_io_full_restore_delta_us",
        "cgroup_io_some_restore_delta_us",
        "cgroup_io_full_restore_delta_us",
        "cgroup_rbytes_restore_delta",
        "memory_current_restore_delta_bytes",
    ):
        pairs = [
            (
                row[
                    feature
                ],
                latency_value,
            )
            for row, latency_value
            in zip(
                cold,
                latency,
            )
            if row[
                feature
            ]
            is not None
        ]

        out[
            feature
        ] = {
            "rho": (
                _spearman(
                    [
                        float(pair[0])
                        for pair
                        in pairs
                    ],
                    [
                        float(pair[1])
                        for pair
                        in pairs
                    ],
                )
                if len(
                    pairs
                )
                >= 3
                else None
            ),
            "n": len(
                pairs
            ),
        }

    return out


def run_panel() -> dict[str, Any]:
    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-019-"
    ) as tmp:
        root = Path(tmp)

        for block in range(
            BLOCKS
        ):
            order = (
                ARMS
                if block % 2 == 0
                else tuple(
                    reversed(
                        ARMS
                    )
                )
            )

            for arm in order:
                rows.append(
                    _trial(
                        root,
                        block=block,
                        arm=arm,
                    )
                )

    warm = [
        row
        for row in rows
        if row[
            "arm"
        ]
        == "WARM_PAGECACHE"
    ]
    cold = [
        row
        for row in rows
        if row[
            "arm"
        ]
        == "COLD_DONTNEED"
    ]

    pre = (
        _analyze_pre_features(
            cold
        )
    )
    diagnostics = (
        _diagnostic_correlations(
            cold
        )
    )

    if pre[
        "significant_features"
    ]:
        route = (
            "PRE_RESTORE_OBSERVABLE_SIGNAL_CANDIDATE"
        )
    else:
        route = (
            "CURRENT_PRE_RESTORE_OBSERVABLES_DO_NOT_EXPLAIN_COLD_LATENCY"
        )

    checks = {
        "paired_blocks_complete": (
            len(warm)
            == BLOCKS
            and len(cold)
            == BLOCKS
        ),
        "all_trials_verify": all(
            row[
                "prepare_verified"
            ]
            and row[
                "restore_verified"
            ]
            for row in rows
        ),
        "warm_resident": all(
            row[
                "pre_resident_fraction"
            ]
            >= 0.95
            for row in warm
        ),
        "cold_nonresident": all(
            row[
                "pre_resident_fraction"
            ]
            <= 0.10
            for row in cold
        ),
        "cold_median_slower": (
            _median_ms(
                cold
            )
            > _median_ms(
                warm
            )
        ),
        "global_psi_available": all(
            row[
                "global_psi_available"
            ]
            for row in rows
        ),
        "memory_current_available": all(
            row[
                "memory_current_available"
            ]
            for row in rows
        ),
        "pre_feature_analysis_completed": (
            len(
                pre[
                    "features"
                ]
            )
            == len(
                PRE_FEATURES
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
            "HOSTED_RESTORE_SYSTEM_OBSERVABILITY_TRACE"
        ),
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "paired_blocks": (
                BLOCKS
            ),
            "pre_window_ms": (
                PRE_WINDOW_MS
            ),
            "permutations": (
                PERMUTATIONS
            ),
        },
        "warm_median_ms": (
            _median_ms(
                warm
            )
        ),
        "cold_median_ms": (
            _median_ms(
                cold
            )
        ),
        "pre_restore_predictive_analysis": (
            pre
        ),
        "restore_window_diagnostics": (
            diagnostics
        ),
        "availability": {
            "cgroup_io_pressure_all_rows": all(
                row[
                    "cgroup_psi_available"
                ]
                for row in rows
            ),
            "cgroup_io_stat_all_rows": all(
                row[
                    "cgroup_io_stat_available"
                ]
                for row in rows
            ),
        },
        "rows": rows,
        "route": route,
        "checks": checks,
        "decision": (
            "SEPARATE_PRE_RESTORE_PREDICTIVE_SIGNALS_FROM_RESTORE_WINDOW_STALL_DIAGNOSTICS"
        ),
        "claim_ceiling": (
            "HOSTED_RESTORE_OBSERVABILITY_PILOT_ONLY"
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
