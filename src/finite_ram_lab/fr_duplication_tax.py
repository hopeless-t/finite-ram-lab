from __future__ import annotations

import argparse
import json
import mmap
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


SCHEMA = "finite-ram-lab.fr-share-001-duplication-tax/v0.1"
PAGE = 4096


def _parse_kib(text: str) -> dict[str, int]:
    result: dict[str, int] = {}

    for raw in text.splitlines():
        if ":" not in raw:
            continue

        key, rest = raw.split(":", 1)
        fields = rest.strip().split()

        if not fields:
            continue

        try:
            result[key] = int(fields[0])
        except ValueError:
            pass

    return result


def _smaps_rollup(pid: int) -> dict[str, int]:
    text = Path(
        f"/proc/{pid}/smaps_rollup"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )

    return _parse_kib(text)


def _write_backing(
    path: Path,
    size_bytes: int,
) -> None:
    pattern = bytes(
        range(256)
    ) * 4096

    remaining = size_bytes

    with path.open("wb") as handle:
        while remaining:
            chunk = pattern[
                : min(
                    len(pattern),
                    remaining,
                )
            ]
            handle.write(chunk)
            remaining -= len(chunk)

        handle.flush()
        os.fsync(
            handle.fileno()
        )


def _touch(
    data,
    size_bytes: int,
) -> int:
    checksum = 0

    for offset in range(
        0,
        size_bytes,
        PAGE,
    ):
        checksum ^= data[offset]

    checksum ^= data[
        size_bytes - 1
    ]

    return int(checksum)


def child(
    mode: str,
    path: Path,
) -> int:
    size_bytes = (
        path.stat().st_size
    )

    payload = None
    mapped = None
    handle = None
    checksum = 0

    if mode == "BASELINE":
        checksum = (
            size_bytes & 0xFF
        )

    elif mode == "PRIVATE_COPY":
        with path.open("rb") as source:
            payload = bytearray(
                source.read()
            )

        checksum = _touch(
            payload,
            size_bytes,
        )

    elif mode == "SHARED_MMAP":
        handle = path.open("rb")
        mapped = mmap.mmap(
            handle.fileno(),
            0,
            access=mmap.ACCESS_READ,
        )

        checksum = _touch(
            mapped,
            size_bytes,
        )

    else:
        raise ValueError(
            f"unknown_mode:{mode}"
        )

    print(
        json.dumps(
            {
                "status": "READY",
                "pid": os.getpid(),
                "mode": mode,
                "checksum": checksum,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    try:
        while True:
            time.sleep(60.0)
    finally:
        if mapped is not None:
            mapped.close()

        if handle is not None:
            handle.close()

    return 0


def _spawn_workers(
    *,
    mode: str,
    path: Path,
    workers: int,
) -> list[subprocess.Popen[str]]:
    processes = []

    try:
        for _ in range(workers):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "finite_ram_lab.fr_duplication_tax",
                    "--child",
                    mode,
                    "--path",
                    str(path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if process.stdout is None:
                raise RuntimeError(
                    "worker_stdout_missing"
                )

            line = (
                process.stdout.readline()
            )

            if not line:
                stderr = (
                    process.stderr.read()
                    if process.stderr
                    is not None
                    else ""
                )

                raise RuntimeError(
                    "worker_not_ready:"
                    f"{mode}:{stderr}"
                )

            message = json.loads(
                line
            )

            if (
                message.get("status")
                != "READY"
            ):
                raise RuntimeError(
                    "worker_bad_ready:"
                    f"{message}"
                )

            processes.append(
                process
            )

        return processes

    except BaseException:
        _stop_workers(
            processes
        )
        raise


def _stop_workers(
    processes: list[
        subprocess.Popen[str]
    ],
) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        try:
            process.wait(
                timeout=5.0
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(
                timeout=5.0
            )


def _measure_arm(
    *,
    mode: str,
    path: Path,
    workers: int,
) -> dict:
    processes = _spawn_workers(
        mode=mode,
        path=path,
        workers=workers,
    )

    try:
        rows = [
            _smaps_rollup(
                process.pid
            )
            for process
            in processes
        ]

        return {
            "mode": mode,
            "workers": workers,
            "sum_pss_kib": sum(
                row.get(
                    "Pss",
                    0,
                )
                for row in rows
            ),
            "sum_rss_kib": sum(
                row.get(
                    "Rss",
                    0,
                )
                for row in rows
            ),
            "sum_private_dirty_kib": (
                sum(
                    row.get(
                        "Private_Dirty",
                        0,
                    )
                    for row
                    in rows
                )
            ),
            "sum_shared_clean_kib": (
                sum(
                    row.get(
                        "Shared_Clean",
                        0,
                    )
                    for row
                    in rows
                )
            ),
            "per_worker_pss_kib": [
                row.get(
                    "Pss",
                    0,
                )
                for row in rows
            ],
        }

    finally:
        _stop_workers(
            processes
        )


def run_experiment(
    *,
    workers: int,
    file_mib: int,
) -> dict:
    if workers < 2:
        raise ValueError(
            "workers_must_be_at_least_two"
        )

    if file_mib < 1:
        raise ValueError(
            "file_mib_must_be_positive"
        )

    size_bytes = (
        file_mib
        * 1024
        * 1024
    )

    with tempfile.TemporaryDirectory(
        prefix="fr-share-001-"
    ) as temp_dir:
        path = (
            Path(temp_dir)
            / "immutable.bin"
        )

        _write_backing(
            path,
            size_bytes,
        )

        baseline = _measure_arm(
            mode="BASELINE",
            path=path,
            workers=workers,
        )

        private = _measure_arm(
            mode="PRIVATE_COPY",
            path=path,
            workers=workers,
        )

        shared = _measure_arm(
            mode="SHARED_MMAP",
            path=path,
            workers=workers,
        )

    private_delta = (
        private["sum_pss_kib"]
        - baseline[
            "sum_pss_kib"
        ]
    )

    shared_delta = (
        shared["sum_pss_kib"]
        - baseline[
            "sum_pss_kib"
        ]
    )

    if private_delta <= 0:
        raise RuntimeError(
            "private_delta_nonpositive"
        )

    if shared_delta <= 0:
        raise RuntimeError(
            "shared_delta_nonpositive"
        )

    ratio = (
        shared_delta
        / private_delta
    )

    theoretical_private_kib = (
        workers
        * file_mib
        * 1024
    )

    theoretical_shared_kib = (
        file_mib
        * 1024
    )

    if (
        private_delta
        < 0.70
        * theoretical_private_kib
    ):
        raise RuntimeError(
            "private_materialization_too_small:"
            f"{private_delta}"
        )

    if (
        shared_delta
        > 2.0
        * theoretical_shared_kib
    ):
        raise RuntimeError(
            "shared_materialization_too_large:"
            f"{shared_delta}"
        )

    if ratio >= 0.35:
        raise RuntimeError(
            "shared_pss_ratio_not_small:"
            f"{ratio}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "PHYSICAL_PROCESS_PSS_DUPLICATION_TAX_VALIDATED"
        ),
        "platform": (
            "LINUX_PROCFS_PROCESS_PSS"
        ),
        "workers": workers,
        "immutable_file_mib": (
            file_mib
        ),
        "arms": {
            "BASELINE": baseline,
            "PRIVATE_COPY": private,
            "SHARED_MMAP": shared,
        },
        "derived": {
            "private_pss_delta_kib": (
                private_delta
            ),
            "shared_pss_delta_kib": (
                shared_delta
            ),
            "shared_over_private_pss_delta_ratio": (
                ratio
            ),
            "pss_delta_reduction_fraction": (
                1.0 - ratio
            ),
            "theoretical_private_payload_kib": (
                theoretical_private_kib
            ),
            "theoretical_shared_payload_kib": (
                theoretical_shared_kib
            ),
            "private_to_shared_theoretical_payload_ratio": (
                workers
            ),
        },
        "interpretation": {
            "rss_warning": (
                "RSS counts shared pages in every process; summed PSS is used to apportion shared physical pages."
            ),
            "pagecache_boundary": (
                "The experiment compares process-attributed PSS. Global page-cache accounting is not fully captured by child PSS, so total-system private-copy cost is not claimed from this measurement."
            ),
            "semantic_boundary": (
                "The payload is immutable bytes. Writable/private model state may not be shareable under the same mechanism."
            ),
        },
        "primary_findings": [
            "DUPLICATION_FACTOR_IS_A_PHYSICAL_MEMORY_CONTROL_VARIABLE",
            "SUMMED_RSS_IS_MISLEADING_FOR_SHARED_IMMUTABLE_STATE",
            "SHARED_FILE_BACKED_MAPPING_CAN_COLLAPSE_MULTIWORKER_PROCESS_PSS",
            "SHARING_CAN_DOMINATE_ADDITIONAL_BITWIDTH_REDUCTION_WHEN_COPY_COUNT_IS_HIGH",
            "IMMUTABILITY_AND_WRITE_SEMANTICS_MUST_BE_FROZEN_BEFORE_SHARING",
        ],
        "claim_ceiling": (
            "HOSTED_LINUX_IMMUTABLE_PROCESS_PSS_SHARING_ONLY"
        ),
    }


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--child",
        choices=(
            "BASELINE",
            "PRIVATE_COPY",
            "SHARED_MMAP",
        ),
        default=None,
    )

    parser.add_argument(
        "--path",
        default=None,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--file-mib",
        type=int,
        default=32,
    )

    args = parser.parse_args(
        argv
    )

    if args.child is not None:
        if args.path is None:
            raise ValueError(
                "child_requires_path"
            )

        return child(
            args.child,
            Path(args.path),
        )

    print(
        json.dumps(
            run_experiment(
                workers=args.workers,
                file_mib=args.file_mib,
            ),
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
