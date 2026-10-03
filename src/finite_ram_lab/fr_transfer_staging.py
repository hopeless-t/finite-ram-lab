from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys


SCHEMA = "finite-ram-lab.fr-xfer-001-staging-peak-tax/v0.1"
PAYLOAD_MIB = 32
REPETITIONS = 4
PAGE = os.sysconf("SC_PAGE_SIZE")

ARMS = (
    "SOURCE_ONLY",
    "DIRECT_COPY",
    "STAGED_COPY",
    "SHARED_VIEW",
)


def _parse_kib(
    text: str,
) -> dict[str, int]:
    result = {}

    for raw in text.splitlines():
        if ":" not in raw:
            continue

        key, rest = raw.split(
            ":",
            1,
        )

        fields = (
            rest.strip()
            .split()
        )

        if not fields:
            continue

        try:
            result[key] = int(
                fields[0]
            )
        except ValueError:
            pass

    return result


def _self_pss_kib() -> int:
    row = _parse_kib(
        Path(
            "/proc/self/smaps_rollup"
        ).read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    return int(
        row["Pss"]
    )


def _touch(
    payload: bytearray,
) -> int:
    checksum = 0

    for offset in range(
        0,
        len(payload),
        PAGE,
    ):
        value = (
            (offset // PAGE)
            % 251
        ) + 1

        payload[offset] = value
        checksum ^= value

    payload[
        len(payload) - 1
    ] = 173

    checksum ^= 173

    return checksum


def run_child(
    *,
    arm: str,
    payload_mib: int,
) -> dict:
    if arm not in ARMS:
        raise ValueError(
            f"unknown_arm:{arm}"
        )

    size_bytes = (
        payload_mib
        * 1024
        * 1024
    )

    gc.collect()

    baseline_pss = (
        _self_pss_kib()
    )

    source = bytearray(
        size_bytes
    )

    checksum = _touch(
        source
    )

    destination = None
    staging = None
    shared_view = None

    if arm == "DIRECT_COPY":
        destination = bytearray(
            source
        )

        checksum ^= (
            destination[0]
        )

    elif arm == "STAGED_COPY":
        staging = bytes(
            source
        )

        destination = bytearray(
            staging
        )

        checksum ^= (
            staging[0]
        )

        checksum ^= (
            destination[0]
        )

    elif arm == "SHARED_VIEW":
        shared_view = (
            memoryview(
                source
            ).toreadonly()
        )

        checksum ^= int(
            shared_view[0]
        )

    held_pss = (
        _self_pss_kib()
    )

    peak_rss_kib = int(
        resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
    )

    pss_delta = (
        held_pss
        - baseline_pss
    )

    payload_kib = (
        payload_mib
        * 1024
    )

    return {
        "schema": SCHEMA,
        "arm": arm,
        "payload_mib": (
            payload_mib
        ),
        "payload_kib": (
            payload_kib
        ),
        "baseline_pss_kib": (
            baseline_pss
        ),
        "held_pss_kib": (
            held_pss
        ),
        "pss_delta_kib": (
            pss_delta
        ),
        "pss_delta_over_payload": (
            pss_delta
            / payload_kib
        ),
        "peak_rss_kib": (
            peak_rss_kib
        ),
        "checksum": checksum,
        "held_objects": {
            "source": True,
            "staging": (
                staging
                is not None
            ),
            "destination": (
                destination
                is not None
            ),
            "shared_view": (
                shared_view
                is not None
            ),
        },
    }


def _run_child_process(
    *,
    arm: str,
    payload_mib: int,
) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finite_ram_lab.fr_transfer_staging",
            "--child",
            "--arm",
            arm,
            "--payload-mib",
            str(
                payload_mib
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return json.loads(
        completed.stdout
    )


def _median(
    values: list[float],
) -> float:
    return float(
        statistics.median(
            values
        )
    )


def run_experiment(
    *,
    payload_mib: int = PAYLOAD_MIB,
    repetitions: int = REPETITIONS,
) -> dict:
    rows = []

    for repetition in range(
        repetitions
    ):
        order = (
            ARMS
            if repetition % 2 == 0
            else tuple(
                reversed(
                    ARMS
                )
            )
        )

        for arm in order:
            row = (
                _run_child_process(
                    arm=arm,
                    payload_mib=(
                        payload_mib
                    ),
                )
            )

            row[
                "repetition"
            ] = repetition

            rows.append(
                row
            )

    aggregate = {}

    for arm in ARMS:
        selected = [
            row
            for row in rows
            if row[
                "arm"
            ] == arm
        ]

        aggregate[arm] = {
            "median_pss_delta_kib": (
                _median(
                    [
                        float(
                            row[
                                "pss_delta_kib"
                            ]
                        )
                        for row
                        in selected
                    ]
                )
            ),
            "median_pss_delta_over_payload": (
                _median(
                    [
                        float(
                            row[
                                "pss_delta_over_payload"
                            ]
                        )
                        for row
                        in selected
                    ]
                )
            ),
            "min_pss_delta_kib": min(
                row[
                    "pss_delta_kib"
                ]
                for row
                in selected
            ),
            "max_pss_delta_kib": max(
                row[
                    "pss_delta_kib"
                ]
                for row
                in selected
            ),
        }

    source = aggregate[
        "SOURCE_ONLY"
    ][
        "median_pss_delta_kib"
    ]

    direct = aggregate[
        "DIRECT_COPY"
    ][
        "median_pss_delta_kib"
    ]

    staged = aggregate[
        "STAGED_COPY"
    ][
        "median_pss_delta_kib"
    ]

    shared = aggregate[
        "SHARED_VIEW"
    ][
        "median_pss_delta_kib"
    ]

    direct_ratio = (
        direct / source
    )

    staged_ratio = (
        staged / source
    )

    shared_ratio = (
        shared / source
    )

    if not (
        0.70
        <= aggregate[
            "SOURCE_ONLY"
        ][
            "median_pss_delta_over_payload"
        ]
        <= 1.35
    ):
        raise RuntimeError(
            "source_materialization_unexpected"
        )

    if not (
        1.60
        <= direct_ratio
        <= 2.40
    ):
        raise RuntimeError(
            "direct_copy_ratio_unexpected:"
            f"{direct_ratio}"
        )

    if not (
        2.50
        <= staged_ratio
        <= 3.50
    ):
        raise RuntimeError(
            "staged_copy_ratio_unexpected:"
            f"{staged_ratio}"
        )

    if not (
        0.80
        <= shared_ratio
        <= 1.20
    ):
        raise RuntimeError(
            "shared_view_ratio_unexpected:"
            f"{shared_ratio}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "HOSTED_LINUX_TRANSFER_STAGING_PSS_PEAK_VALIDATED"
        ),
        "fixture": {
            "payload_mib": (
                payload_mib
            ),
            "repetitions": (
                repetitions
            ),
            "fresh_process_per_arm": (
                True
            ),
            "page_size": PAGE,
        },
        "rows": rows,
        "aggregate": (
            aggregate
        ),
        "derived": {
            "direct_over_source_pss_ratio": (
                direct_ratio
            ),
            "staged_over_source_pss_ratio": (
                staged_ratio
            ),
            "shared_view_over_source_pss_ratio": (
                shared_ratio
            ),
            "staging_tax_over_direct_fraction": (
                staged
                / direct
                - 1.0
            ),
            "shared_view_saving_vs_staged_fraction": (
                1.0
                - shared
                / staged
            ),
        },
        "primary_findings": [
            "TRANSFER_CAN_CREATE_A_TRANSIENT_RESIDENCY_PEAK_LARGER_THAN_SOURCE_OR_DESTINATION_ALONE",
            "EXPLICIT_STAGING_CAN_APPROACH_SOURCE_PLUS_STAGING_PLUS_DESTINATION_GEOMETRY",
            "DIRECT_COPY_CAN_APPROACH_SOURCE_PLUS_DESTINATION_GEOMETRY",
            "ZERO_COPY_VIEW_CAN_AVOID_PAYLOAD_DUPLICATION_WHEN_SEMANTICS_ALLOW_SHARING",
            "A_MEMORY_SAVING_TIER_MIGRATION_CAN_FAIL_IF_ITS_TRANSIENT_PEAK_CROSSES_THE_PRESSURE_KNEE",
            "TRANSFER_STAGING_MUST_BE_BUDGETED_AS_AN_INDEPENDENT_ATOM",
        ],
        "boundaries": {
            "scope": (
                "Python host-memory copy/view proxy on a GitHub-hosted Linux runner."
            ),
            "not_claimed": [
                "CUDA DMA",
                "pinned-memory behavior",
                "RAM-to-VRAM bandwidth",
                "PCIe tail latency",
                "zero-copy GPU execution",
                "development-machine thresholds",
            ],
        },
        "claim_ceiling": (
            "HOSTED_LINUX_PYTHON_TRANSFER_STAGING_PROXY_ONLY"
        ),
    }


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--child",
        action="store_true",
    )

    parser.add_argument(
        "--arm",
        choices=ARMS,
    )

    parser.add_argument(
        "--payload-mib",
        type=int,
        default=PAYLOAD_MIB,
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=REPETITIONS,
    )

    args = parser.parse_args(
        argv
    )

    if args.child:
        if args.arm is None:
            raise ValueError(
                "child_requires_arm"
            )

        print(
            json.dumps(
                run_child(
                    arm=args.arm,
                    payload_mib=(
                        args.payload_mib
                    ),
                ),
                sort_keys=True,
            )
        )

        return 0

    print(
        json.dumps(
            run_experiment(
                payload_mib=(
                    args.payload_mib
                ),
                repetitions=(
                    args.repetitions
                ),
            ),
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
