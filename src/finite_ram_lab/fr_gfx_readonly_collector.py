from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import TextIO

from finite_ram_lab.fr_gfx_observation_plane import (
    parse_kib_table,
    parse_psi,
)


SCHEMA = "finite-ram-lab.fr-gfx-006-readonly-collector/v0.1"


def _read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def _current_rss_kib(
    pid: int,
) -> int | None:
    status = parse_kib_table(
        _read_text(
            Path(
                f"/proc/{pid}/status"
            )
        )
    )

    return status.get(
        "VmRSS"
    )


def collect_once(
    target_pid: int,
) -> dict:
    timestamp_ns = (
        time.monotonic_ns()
    )

    meminfo = parse_kib_table(
        _read_text(
            Path(
                "/proc/meminfo"
            )
        )
    )

    psi = parse_psi(
        _read_text(
            Path(
                "/proc/pressure/memory"
            )
        )
    )

    smaps_path = Path(
        f"/proc/{target_pid}/smaps_rollup"
    )

    smaps = parse_kib_table(
        _read_text(
            smaps_path
        )
    )

    return {
        "schema": SCHEMA,
        "timestamp_monotonic_ns": (
            timestamp_ns
        ),
        "target_pid": target_pid,
        "process": {
            "rss_kib": smaps.get(
                "Rss"
            ),
            "pss_kib": smaps.get(
                "Pss"
            ),
            "swap_kib": smaps.get(
                "Swap"
            ),
            "private_clean_kib": (
                smaps.get(
                    "Private_Clean"
                )
            ),
            "private_dirty_kib": (
                smaps.get(
                    "Private_Dirty"
                )
            ),
        },
        "system": {
            "mem_total_kib": (
                meminfo.get(
                    "MemTotal"
                )
            ),
            "mem_available_kib": (
                meminfo.get(
                    "MemAvailable"
                )
            ),
            "swap_total_kib": (
                meminfo.get(
                    "SwapTotal"
                )
            ),
            "swap_free_kib": (
                meminfo.get(
                    "SwapFree"
                )
            ),
        },
        "pressure": {
            "memory_some_avg10": (
                psi.get(
                    "some_avg10"
                )
            ),
            "memory_full_avg10": (
                psi.get(
                    "full_avg10"
                )
            ),
            "memory_some_total_us": (
                psi.get(
                    "some_total"
                )
            ),
            "memory_full_total_us": (
                psi.get(
                    "full_total"
                )
            ),
        },
        "external": {
            "frame": None,
            "gpu": None,
            "backend": None,
            "note": (
                "FR-GFX-006 does not launch or inject frame/GPU tools; external streams are joined by a later adapter."
            ),
        },
    }


def run_collection(
    *,
    target_pid: int,
    samples: int,
    interval_ms: float,
    output: TextIO,
) -> dict:
    if samples < 1:
        raise ValueError(
            "samples_must_be_positive"
        )

    if interval_ms < 0.0:
        raise ValueError(
            "interval_must_be_nonnegative"
        )

    self_pid = os.getpid()
    wall_start = (
        time.perf_counter()
    )
    cpu_start = (
        time.process_time()
    )

    output_bytes = 0
    max_collector_rss_kib = (
        _current_rss_kib(
            self_pid
        )
    )

    first_timestamp = None
    last_timestamp = None

    for index in range(
        samples
    ):
        row = collect_once(
            target_pid
        )

        if first_timestamp is None:
            first_timestamp = row[
                "timestamp_monotonic_ns"
            ]

        last_timestamp = row[
            "timestamp_monotonic_ns"
        ]

        line = (
            json.dumps(
                row,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
            )
            + "\n"
        )

        output.write(line)
        output.flush()

        output_bytes += len(
            line.encode(
                "utf-8"
            )
        )

        rss = _current_rss_kib(
            self_pid
        )

        if rss is not None:
            if (
                max_collector_rss_kib
                is None
                or rss
                > max_collector_rss_kib
            ):
                max_collector_rss_kib = (
                    rss
                )

        if (
            index + 1
            < samples
            and interval_ms
            > 0.0
        ):
            time.sleep(
                interval_ms
                / 1000.0
            )

    cpu_end = (
        time.process_time()
    )
    wall_end = (
        time.perf_counter()
    )

    wall_seconds = (
        wall_end - wall_start
    )

    cpu_seconds = (
        cpu_end - cpu_start
    )

    return {
        "schema": (
            "finite-ram-lab.fr-gfx-006-collector-receipt/v0.1"
        ),
        "target_pid": target_pid,
        "collector_pid": self_pid,
        "samples": samples,
        "interval_ms": (
            interval_ms
        ),
        "first_timestamp_monotonic_ns": (
            first_timestamp
        ),
        "last_timestamp_monotonic_ns": (
            last_timestamp
        ),
        "wall_seconds": (
            wall_seconds
        ),
        "collector_cpu_seconds": (
            cpu_seconds
        ),
        "collector_cpu_pct_one_core": (
            None
            if wall_seconds
            <= 0.0
            else (
                cpu_seconds
                / wall_seconds
                * 100.0
            )
        ),
        "collector_peak_observed_rss_kib": (
            max_collector_rss_kib
        ),
        "jsonl_bytes": output_bytes,
        "bytes_per_sample": (
            output_bytes
            / samples
        ),
        "read_only_contract": {
            "writes_sysfs": False,
            "changes_game_settings": False,
            "changes_driver_settings": False,
            "injects_target_process": False,
            "signals_target_process": False,
            "launches_gpu_telemetry": False,
            "launches_frame_telemetry": False,
            "writes_only_requested_output_stream": True,
        },
        "qualification": (
            "MEASUREMENT_ONLY_NO_LIVE_PERTURBATION_THRESHOLD"
        ),
    }


def _parse_pid(
    value: str,
) -> int:
    if value == "self":
        return os.getpid()

    pid = int(value)

    if pid <= 0:
        raise ValueError(
            "pid_must_be_positive"
        )

    return pid


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pid",
        required=True,
        help=(
            "Target PID or 'self'."
        ),
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--interval-ms",
        type=float,
        default=500.0,
    )

    parser.add_argument(
        "--output",
        default="-",
        help=(
            "JSONL output path, or '-' for stdout."
        ),
    )

    parser.add_argument(
        "--receipt",
        default=None,
        help=(
            "Optional receipt JSON path."
        ),
    )

    args = parser.parse_args(
        argv
    )

    target_pid = _parse_pid(
        args.pid
    )

    output_handle: TextIO

    if args.output == "-":
        output_handle = sys.stdout
        should_close = False
    else:
        output_path = Path(
            args.output
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_handle = output_path.open(
            "w",
            encoding="utf-8",
        )

        should_close = True

    try:
        receipt = run_collection(
            target_pid=target_pid,
            samples=args.samples,
            interval_ms=(
                args.interval_ms
            ),
            output=output_handle,
        )
    finally:
        if should_close:
            output_handle.close()

    receipt_text = json.dumps(
        receipt,
        sort_keys=True,
        indent=2,
    )

    if args.receipt is None:
        print(
            receipt_text,
            file=sys.stderr,
        )
    else:
        receipt_path = Path(
            args.receipt
        )

        receipt_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        receipt_path.write_text(
            receipt_text + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
