from __future__ import annotations

import json
import mmap
import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.strata001_probe import (
    _fadvise_dontneed,
    _file_residency,
)

SCHEMA = "finite-ram-lab.fr-fp-016-restore-size-scaling/v0.1"

STATE_SIZES_MIB = (
    4,
    8,
    16,
)
BLOCKS = 6
ARMS = (
    "WARM_PAGECACHE",
    "COLD_DONTNEED",
)

REPLICATION_HISTORY = {
    "run_37145768871": {
        "warm_r2": 0.9871319562539695,
        "cold_r2": 0.9139812532802742,
        "cold_slope_4_to_8_ns_per_mib": 336042.375,
        "cold_slope_8_to_16_ns_per_mib": 3977966.3125,
    },
    "run_37145960094": {
        "warm_r2": 0.9993036627559178,
        "cold_r2": 0.7303830590200129,
        "cold_slope_4_to_8_ns_per_mib": 28303037.625,
        "cold_slope_8_to_16_ns_per_mib": 3067139.8125,
        "cold_cv": {
            "4": 1.0823148185981186,
            "8": 0.7659077620604521,
            "16": 0.6117185993017832,
        },
    },
}
WRITE_CHUNK_BYTES = (
    1024
    * 1024
)


def _size_bytes(
    size_mib: int,
) -> int:
    return (
        size_mib
        * 1024
        * 1024
    )


def _fault_region(
    *,
    size_bytes: int,
    marker: int,
) -> mmap.mmap:
    region = mmap.mmap(
        -1,
        size_bytes,
        flags=(
            mmap.MAP_PRIVATE
            | mmap.MAP_ANONYMOUS
        ),
        prot=(
            mmap.PROT_READ
            | mmap.PROT_WRITE
        ),
    )

    page_size = os.sysconf(
        "SC_PAGE_SIZE"
    )
    value = (
        marker
        % 251
        + 1
    )

    for offset in range(
        0,
        size_bytes,
        page_size,
    ):
        region[
            offset
        ] = value

    return region


def _sentinel_offsets(
    size_bytes: int,
) -> tuple[int, int, int]:
    page_size = os.sysconf(
        "SC_PAGE_SIZE"
    )
    middle = (
        size_bytes // 2
        // page_size
    ) * page_size

    return (
        0,
        middle,
        size_bytes
        - page_size,
    )


def _verify_fd(
    fd: int,
    *,
    size_bytes: int,
    marker: int,
) -> bool:
    expected = bytes(
        [
            marker
            % 251
            + 1
        ]
    )

    return all(
        os.pread(
            fd,
            1,
            offset,
        )
        == expected
        for offset
        in _sentinel_offsets(
            size_bytes
        )
    )


def _verify_mapping(
    region: mmap.mmap,
    *,
    size_bytes: int,
    marker: int,
) -> bool:
    expected = (
        marker
        % 251
        + 1
    )

    return all(
        region[
            offset
        ]
        == expected
        for offset
        in _sentinel_offsets(
            size_bytes
        )
    )


def _prepare_tier(
    path: Path,
    *,
    size_bytes: int,
    marker: int,
    cold: bool,
) -> dict[str, Any]:
    region = _fault_region(
        size_bytes=size_bytes,
        marker=marker,
    )

    fd = os.open(
        path,
        os.O_RDWR
        | os.O_CREAT
        | os.O_TRUNC,
        0o600,
    )

    written = 0
    start = time.perf_counter_ns()

    try:
        while written < size_bytes:
            end = min(
                written
                + WRITE_CHUNK_BYTES,
                size_bytes,
            )
            chunk = region[
                written:end
            ]
            offset = 0

            while offset < len(
                chunk
            ):
                count = os.write(
                    fd,
                    chunk[
                        offset:
                    ],
                )

                if count <= 0:
                    raise RuntimeError(
                        "short_prepare_write"
                    )

                offset += count
                written += count

        os.fsync(fd)
        verified = _verify_fd(
            fd,
            size_bytes=size_bytes,
            marker=marker,
        )

        region.close()

        advice_called = False

        if cold:
            if (
                not hasattr(
                    os,
                    "posix_fadvise",
                )
                or not hasattr(
                    os,
                    "POSIX_FADV_DONTNEED",
                )
            ):
                raise RuntimeError(
                    "POSIX_FADV_DONTNEED unavailable"
                )

            os.posix_fadvise(
                fd,
                0,
                size_bytes,
                os.POSIX_FADV_DONTNEED,
            )
            advice_called = True
            time.sleep(
                0.01
            )

        return {
            "bytes_written": (
                written
            ),
            "verified": (
                verified
            ),
            "advice_called": (
                advice_called
            ),
            "prepare_ns": (
                time.perf_counter_ns()
                - start
            ),
        }

    finally:
        os.close(fd)


def _restore(
    path: Path,
    *,
    size_bytes: int,
    marker: int,
) -> dict[str, Any]:
    region = mmap.mmap(
        -1,
        size_bytes,
        flags=(
            mmap.MAP_PRIVATE
            | mmap.MAP_ANONYMOUS
        ),
        prot=(
            mmap.PROT_READ
            | mmap.PROT_WRITE
        ),
    )

    fd = os.open(
        path,
        os.O_RDONLY,
    )
    view = memoryview(
        region
    )

    try:
        start = (
            time.perf_counter_ns()
        )
        got = os.preadv(
            fd,
            [view],
            0,
        )
        end = (
            time.perf_counter_ns()
        )
    finally:
        view.release()
        os.close(fd)

    verified = (
        got == size_bytes
        and _verify_mapping(
            region,
            size_bytes=size_bytes,
            marker=marker,
        )
    )

    region.close()

    return {
        "bytes_read": (
            got
        ),
        "read_ns": (
            end - start
        ),
        "verified": (
            verified
        ),
    }


def _fit(
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
    slope = (
        sum(
            (x - x_mean)
            * (y - y_mean)
            for x, y
            in zip(
                xs,
                ys,
            )
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
    ss_res = sum(
        (
            y
            - prediction
        ) ** 2
        for y, prediction
        in zip(
            ys,
            predictions,
        )
    )
    ss_tot = sum(
        (
            y
            - y_mean
        ) ** 2
        for y in ys
    )

    r2 = (
        1.0
        if ss_tot == 0.0
        else 1.0
        - ss_res
        / ss_tot
    )

    bandwidth_mib_s = (
        float("inf")
        if slope <= 0.0
        else (
            1_000_000_000.0
            / slope
        )
    )

    return {
        "slope_ns_per_mib": (
            slope
        ),
        "intercept_ns": (
            intercept
        ),
        "r2": r2,
        "effective_bandwidth_mib_s": (
            bandwidth_mib_s
        ),
    }


def run_trial(
    *,
    block: int,
    size_mib: int,
    arm: str,
    root: Path,
) -> dict[str, Any]:
    size_bytes = _size_bytes(
        size_mib
    )
    marker = (
        block
        + size_mib
    )
    path = root / (
        f"b{block:02d}-"
        f"{size_mib:02d}m-"
        f"{arm}.bin"
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

    pre = _file_residency(
        path
    )

    restored = _restore(
        path,
        size_bytes=size_bytes,
        marker=marker,
    )

    _fadvise_dontneed(
        path
    )
    path.unlink()
    time.sleep(
        0.003
    )

    return {
        "block": block,
        "size_mib": (
            size_mib
        ),
        "arm": arm,
        "prepare": (
            prepared
        ),
        "pre_restore_residency": (
            pre
        ),
        "restore": (
            restored
        ),
    }


def run_panel() -> dict[str, Any]:
    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-016-"
    ) as tmp:
        root = Path(tmp)

        for block in range(
            BLOCKS
        ):
            for size_index, size_mib in enumerate(
                STATE_SIZES_MIB
            ):
                order = (
                    ARMS
                    if (
                        block
                        + size_index
                    )
                    % 2
                    == 0
                    else tuple(
                        reversed(
                            ARMS
                        )
                    )
                )

                for arm in order:
                    rows.append(
                        run_trial(
                            block=block,
                            size_mib=(
                                size_mib
                            ),
                            arm=arm,
                            root=root,
                        )
                    )

    medians: dict[str, Any] = {
        arm: {}
        for arm in ARMS
    }

    for arm in ARMS:
        for size_mib in (
            STATE_SIZES_MIB
        ):
            selected = [
                row
                for row in rows
                if (
                    row[
                        "arm"
                    ]
                    == arm
                    and row[
                        "size_mib"
                    ]
                    == size_mib
                )
            ]

            medians[arm][
                str(
                    size_mib
                )
            ] = {
                "read_ns": (
                    statistics.median(
                        row[
                            "restore"
                        ][
                            "read_ns"
                        ]
                        for row
                        in selected
                    )
                ),
                "pre_resident_fraction": (
                    statistics.median(
                        row[
                            "pre_restore_residency"
                        ][
                            "resident_fraction"
                        ]
                        for row
                        in selected
                    )
                ),
            }

    xs = [
        float(
            value
        )
        for value in (
            STATE_SIZES_MIB
        )
    ]

    fits = {}

    for arm in ARMS:
        ys = [
            float(
                medians[
                    arm
                ][
                    str(
                        size_mib
                    )
                ][
                    "read_ns"
                ]
            )
            for size_mib
            in STATE_SIZES_MIB
        ]

        fits[arm] = _fit(
            xs,
            ys,
        )

    ratios = {
        str(size_mib): (
            medians[
                "COLD_DONTNEED"
            ][
                str(
                    size_mib
                )
            ][
                "read_ns"
            ]
            / medians[
                "WARM_PAGECACHE"
            ][
                str(
                    size_mib
                )
            ][
                "read_ns"
            ]
        )
        for size_mib
        in STATE_SIZES_MIB
    }

    warm_times = [
        medians[
            "WARM_PAGECACHE"
        ][
            str(
                size_mib
            )
        ][
            "read_ns"
        ]
        for size_mib
        in STATE_SIZES_MIB
    ]
    cold_times = [
        medians[
            "COLD_DONTNEED"
        ][
            str(
                size_mib
            )
        ][
            "read_ns"
        ]
        for size_mib
        in STATE_SIZES_MIB
    ]

    checks = {
        "all_trials_verify": all(
            row[
                "prepare"
            ][
                "verified"
            ]
            and row[
                "restore"
            ][
                "verified"
            ]
            for row in rows
        ),
        "all_warm_pre_resident": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            >= 0.95
            for row in rows
            if row[
                "arm"
            ]
            == "WARM_PAGECACHE"
        ),
        "all_cold_pre_nonresident": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            <= 0.10
            for row in rows
            if row[
                "arm"
            ]
            == "COLD_DONTNEED"
        ),
        "cold_slower_at_every_size": all(
            ratios[
                str(
                    size_mib
                )
            ]
            > 1.0
            for size_mib
            in STATE_SIZES_MIB
        ),
        "warm_latency_increases_with_size": (
            warm_times
            == sorted(
                warm_times
            )
            and len(
                set(
                    warm_times
                )
            )
            == len(
                warm_times
            )
        ),
        "current_warm_fit_reasonable": (
            fits[
                "WARM_PAGECACHE"
            ][
                "r2"
            ]
            > 0.95
        ),
        "warm_linear_behavior_replicated_twice": all(
            row[
                "warm_r2"
            ]
            > 0.98
            for row
            in REPLICATION_HISTORY.values()
        ),
        "cold_single_linear_model_failed_twice": all(
            row[
                "cold_r2"
            ]
            < 0.95
            for row
            in REPLICATION_HISTORY.values()
        ),
        "specific_knee_location_failed_to_replicate": (
            REPLICATION_HISTORY[
                "run_37145768871"
            ][
                "cold_slope_8_to_16_ns_per_mib"
            ]
            > 5.0
            * REPLICATION_HISTORY[
                "run_37145768871"
            ][
                "cold_slope_4_to_8_ns_per_mib"
            ]
            and REPLICATION_HISTORY[
                "run_37145960094"
            ][
                "cold_slope_8_to_16_ns_per_mib"
            ]
            < REPLICATION_HISTORY[
                "run_37145960094"
            ][
                "cold_slope_4_to_8_ns_per_mib"
            ]
        ),
        "second_run_cold_dispersion_is_material": all(
            value
            > 0.60
            for value
            in REPLICATION_HISTORY[
                "run_37145960094"
            ][
                "cold_cv"
            ].values()
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
            "HOSTED_LINUX_WARM_COLD_RESTORE_SIZE_SCALING"
        ),
        "blocks": BLOCKS,
        "state_sizes_mib": list(
            STATE_SIZES_MIB
        ),
        "medians": medians,
        "fits": fits,
        "cold_over_warm_median_read_ratios": (
            ratios
        ),
        "observations": {
            "cold_latency_increases_with_size_this_run": (
                cold_times
                == sorted(
                    cold_times
                )
                and len(
                    set(
                        cold_times
                    )
                )
                == len(
                    cold_times
                )
            ),
            "cold_medians_ns_this_run": {
                str(size_mib): (
                    medians[
                        "COLD_DONTNEED"
                    ][
                        str(size_mib)
                    ][
                        "read_ns"
                    ]
                )
                for size_mib
                in STATE_SIZES_MIB
            },
        },
        "cold_piecewise": {
            "slope_4_to_8_ns_per_mib": (
                (
                    medians[
                        "COLD_DONTNEED"
                    ][
                        "8"
                    ][
                        "read_ns"
                    ]
                    - medians[
                        "COLD_DONTNEED"
                    ][
                        "4"
                    ][
                        "read_ns"
                    ]
                )
                / 4.0
            ),
            "slope_8_to_16_ns_per_mib": (
                (
                    medians[
                        "COLD_DONTNEED"
                    ][
                        "16"
                    ][
                        "read_ns"
                    ]
                    - medians[
                        "COLD_DONTNEED"
                    ][
                        "8"
                    ][
                        "read_ns"
                    ]
                )
                / 8.0
            ),
        },
        "rows": [
            {
                "block": row["block"],
                "size_mib": row["size_mib"],
                "arm": row["arm"],
                "pre_resident_fraction": (
                    row[
                        "pre_restore_residency"
                    ][
                        "resident_fraction"
                    ]
                ),
                "read_ns": (
                    row[
                        "restore"
                    ][
                        "read_ns"
                    ]
                ),
                "verified": (
                    row[
                        "restore"
                    ][
                        "verified"
                    ]
                ),
            }
            for row in rows
        ],
        "replication_history": REPLICATION_HISTORY,
        "checks": checks,
        "decision": (
            "REJECT_SINGLE_STATIONARY_COLD_RESTORE_SIZE_MODEL_AND_MEASURE_COLD_LATENCY_AS_A_DISTRIBUTION_WITH_TEMPORAL_STRUCTURE"
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_WARM_COLD_RESTORE_SIZE_SCALING_ONLY"
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
