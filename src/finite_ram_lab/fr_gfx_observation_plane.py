from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


SCHEMA = "finite-ram-lab.fr-gfx-002-readonly-observation-plane/v0.1"
SEED = "FR-GFX-002-v0.1"
EPISODES = 16_384
FPS_ONLY_THRESHOLD_MS = 34.592


def parse_kib_table(text: str) -> dict[str, int]:
    result: dict[str, int] = {}

    for raw in text.splitlines():
        line = raw.strip()

        if not line or ":" not in line:
            continue

        key, rest = line.split(":", 1)
        fields = rest.strip().split()

        if not fields:
            continue

        try:
            value = int(fields[0])
        except ValueError:
            continue

        result[key] = value

    return result


def parse_psi(text: str) -> dict[str, float]:
    result: dict[str, float] = {}

    for raw in text.splitlines():
        fields = raw.strip().split()

        if not fields:
            continue

        prefix = fields[0]

        for item in fields[1:]:
            if "=" not in item:
                continue

            key, value = item.split("=", 1)

            try:
                numeric = float(value)
            except ValueError:
                continue

            result[f"{prefix}_{key}"] = numeric

    return result


def normalize_observation(
    *,
    timestamp_ns: int,
    frame_ms: float,
    fps: float,
    meminfo_text: str,
    smaps_rollup_text: str,
    psi_memory_text: str,
    intel_gpu_sample: dict,
    backend: dict,
) -> dict:
    meminfo = parse_kib_table(
        meminfo_text
    )

    smaps = parse_kib_table(
        smaps_rollup_text
    )

    psi = parse_psi(
        psi_memory_text
    )

    return {
        "schema": SCHEMA,
        "timestamp_ns": timestamp_ns,
        "frame": {
            "frametime_ms": frame_ms,
            "fps": fps,
        },
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
        },
        "gpu": {
            "render_busy_pct": (
                intel_gpu_sample.get(
                    "render_busy_pct"
                )
            ),
            "frequency_mhz": (
                intel_gpu_sample.get(
                    "frequency_mhz"
                )
            ),
            "memory_read_mib_s": (
                intel_gpu_sample.get(
                    "memory_read_mib_s"
                )
            ),
            "memory_write_mib_s": (
                intel_gpu_sample.get(
                    "memory_write_mib_s"
                )
            ),
        },
        "backend": backend,
    }


def _u(
    episode: int,
    domain: str,
) -> float:
    value = int.from_bytes(
        hashlib.sha256(
            (
                f"{SEED}|{domain}|"
                f"{episode}"
            ).encode(
                "utf-8"
            )
        ).digest()[:8],
        "big",
    )

    return (
        value
        / float(
            (1 << 64) - 1
        )
    )


def _noise(
    episode: int,
    domain: str,
    amplitude: float,
) -> float:
    return (
        _u(
            episode,
            domain,
        )
        - 0.5
    ) * 2.0 * amplitude


@dataclass(frozen=True)
class SyntheticObservation:
    state: str
    frame_ms: float
    gpu_busy: float
    mem_available_mib: float
    psi_some_avg10: float
    cpu_busy: float
    compiler_active: bool


def _sample(
    episode: int,
) -> SyntheticObservation:
    state_draw = _u(
        episode,
        "state",
    )

    if state_draw < 0.50:
        state = "NORMAL"
    elif state_draw < 0.72:
        state = "GPU_BOUND"
    elif state_draw < 0.90:
        state = "UMA_PRESSURE"
    else:
        state = "CPU_DRIVER"

    if state == "NORMAL":
        frame_ms = (
            22.0
            + _noise(
                episode,
                "frame",
                5.0,
            )
        )
        gpu_busy = (
            58.0
            + _noise(
                episode,
                "gpu",
                20.0,
            )
        )
        mem_available = (
            2600.0
            + _noise(
                episode,
                "mem",
                700.0,
            )
        )
        psi = max(
            0.0,
            0.3
            + _noise(
                episode,
                "psi",
                0.5,
            ),
        )
        cpu_busy = (
            45.0
            + _noise(
                episode,
                "cpu",
                20.0,
            )
        )
        compiler = False

    elif state == "GPU_BOUND":
        frame_ms = (
            42.0
            + _noise(
                episode,
                "frame",
                10.0,
            )
        )
        gpu_busy = (
            94.0
            + _noise(
                episode,
                "gpu",
                7.0,
            )
        )
        mem_available = (
            1800.0
            + _noise(
                episode,
                "mem",
                700.0,
            )
        )
        psi = max(
            0.0,
            0.8
            + _noise(
                episode,
                "psi",
                0.9,
            ),
        )
        cpu_busy = (
            50.0
            + _noise(
                episode,
                "cpu",
                18.0,
            )
        )
        compiler = False

    elif state == "UMA_PRESSURE":
        frame_ms = (
            44.0
            + _noise(
                episode,
                "frame",
                11.0,
            )
        )
        gpu_busy = (
            76.0
            + _noise(
                episode,
                "gpu",
                15.0,
            )
        )
        mem_available = (
            450.0
            + _noise(
                episode,
                "mem",
                350.0,
            )
        )
        psi = max(
            0.0,
            10.0
            + _noise(
                episode,
                "psi",
                8.0,
            ),
        )
        cpu_busy = (
            56.0
            + _noise(
                episode,
                "cpu",
                18.0,
            )
        )
        compiler = False

    else:
        frame_ms = (
            41.0
            + _noise(
                episode,
                "frame",
                12.0,
            )
        )
        gpu_busy = (
            53.0
            + _noise(
                episode,
                "gpu",
                20.0,
            )
        )
        mem_available = (
            1800.0
            + _noise(
                episode,
                "mem",
                700.0,
            )
        )
        psi = max(
            0.0,
            1.0
            + _noise(
                episode,
                "psi",
                1.2,
            ),
        )
        cpu_busy = (
            96.0
            + _noise(
                episode,
                "cpu",
                6.0,
            )
        )
        compiler = (
            _u(
                episode,
                "compiler",
            )
            < 0.25
        )

    return SyntheticObservation(
        state=state,
        frame_ms=frame_ms,
        gpu_busy=gpu_busy,
        mem_available_mib=(
            mem_available
        ),
        psi_some_avg10=psi,
        cpu_busy=cpu_busy,
        compiler_active=compiler,
    )


def _target_action(
    state: str,
) -> str:
    return {
        "NORMAL": "OBSERVE",
        "GPU_BOUND": "DOWNSCALE_RENDER",
        "UMA_PRESSURE": "DROP_RESIDENCY",
        "CPU_DRIVER": "CPU_DRIVER_OBSERVE",
    }[state]


def _fps_only(
    row: SyntheticObservation,
) -> str:
    if (
        row.frame_ms
        > FPS_ONLY_THRESHOLD_MS
    ):
        return "DOWNSCALE_RENDER"

    return "OBSERVE"


def _multi_signal(
    row: SyntheticObservation,
) -> str:
    if row.frame_ms <= 33.3:
        return "OBSERVE"

    if (
        row.mem_available_mib
        < 800.0
        or row.psi_some_avg10
        > 5.0
    ):
        return "DROP_RESIDENCY"

    if row.gpu_busy > 88.0:
        return "DOWNSCALE_RENDER"

    if (
        row.cpu_busy > 90.0
        or row.compiler_active
    ):
        return "CPU_DRIVER_OBSERVE"

    return "OBSERVE"


def _accuracy(
    samples: list[
        SyntheticObservation
    ],
    predictor,
) -> float:
    return (
        sum(
            predictor(row)
            == _target_action(
                row.state
            )
            for row in samples
        )
        / len(samples)
    )


def _gpu_stats(
    samples: list[
        SyntheticObservation
    ],
    predictor,
) -> tuple[
    float,
    float,
]:
    gpu_rows = [
        row
        for row in samples
        if row.state
        == "GPU_BOUND"
    ]

    non_gpu = [
        row
        for row in samples
        if row.state
        != "GPU_BOUND"
    ]

    recall = (
        sum(
            predictor(row)
            == "DOWNSCALE_RENDER"
            for row in gpu_rows
        )
        / len(gpu_rows)
    )

    fpr = (
        sum(
            predictor(row)
            == "DOWNSCALE_RENDER"
            for row in non_gpu
        )
        / len(non_gpu)
    )

    return recall, fpr


def run_panel() -> dict:
    samples = [
        _sample(
            episode
        )
        for episode in range(
            EPISODES
        )
    ]

    counts = {
        state: sum(
            row.state
            == state
            for row in samples
        )
        for state in (
            "NORMAL",
            "GPU_BOUND",
            "UMA_PRESSURE",
            "CPU_DRIVER",
        )
    }

    fps_accuracy = _accuracy(
        samples,
        _fps_only,
    )

    multi_accuracy = _accuracy(
        samples,
        _multi_signal,
    )

    (
        fps_recall,
        fps_fpr,
    ) = _gpu_stats(
        samples,
        _fps_only,
    )

    (
        multi_recall,
        multi_fpr,
    ) = _gpu_stats(
        samples,
        _multi_signal,
    )

    frozen = {
        "counts": {
            "NORMAL": 8252,
            "GPU_BOUND": 3676,
            "UMA_PRESSURE": 2850,
            "CPU_DRIVER": 1606,
        },
        "fps_accuracy": (
            0.69696044921875
        ),
        "multi_accuracy": (
            0.94921875
        ),
        "gpu_recall": (
            0.8615342763873776
        ),
        "fps_gpu_fpr": (
            0.3060276990871892
        ),
        "multi_gpu_fpr": 0.0,
    }

    actual = {
        "counts": counts,
        "fps_accuracy": (
            fps_accuracy
        ),
        "multi_accuracy": (
            multi_accuracy
        ),
        "gpu_recall": (
            multi_recall
        ),
        "fps_gpu_fpr": (
            fps_fpr
        ),
        "multi_gpu_fpr": (
            multi_fpr
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            (
                "frozen_identifiability_"
                f"result_changed:{actual}"
            )
        )

    if (
        abs(
            fps_recall
            - multi_recall
        )
        > 1e-15
    ):
        raise RuntimeError(
            "gpu_recall_not_matched"
        )

    fixture = normalize_observation(
        timestamp_ns=123456789,
        frame_ms=100.0,
        fps=10.0,
        meminfo_text=(
            "MemTotal: 20000000 kB\n"
            "MemAvailable: 3500000 kB\n"
            "SwapTotal: 4000000 kB\n"
            "SwapFree: 2500000 kB\n"
        ),
        smaps_rollup_text=(
            "Rss: 1450000 kB\n"
            "Pss: 1310000 kB\n"
            "Swap: 120000 kB\n"
        ),
        psi_memory_text=(
            "some avg10=3.25 "
            "avg60=1.50 "
            "avg300=0.50 "
            "total=1000\n"
            "full avg10=0.75 "
            "avg60=0.25 "
            "avg300=0.10 "
            "total=200\n"
        ),
        intel_gpu_sample={
            "render_busy_pct": (
                96.0
            ),
            "frequency_mhz": (
                1050.0
            ),
            "memory_read_mib_s": (
                4200.0
            ),
            "memory_write_mib_s": (
                1100.0
            ),
        },
        backend={
            "translation": "DXVK",
            "api": "D3D11",
            "proton": "UNKNOWN",
        },
    )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "READ_ONLY_OBSERVATION_SCHEMA_PLUS_SIGNAL_IDENTIFIABILITY_VALIDATED"
        ),
        "read_only_contract": {
            "writes_sysfs": False,
            "changes_driver_settings": False,
            "changes_game_settings": False,
            "injects_game_process": False,
            "kills_processes": False,
        },
        "source_classes": {
            "frame": (
                "MangoHud or equivalent present/frame logger"
            ),
            "gpu": (
                "intel_gpu_top JSON/CSV on supported i915 systems"
            ),
            "system_memory": (
                "/proc/meminfo"
            ),
            "process_memory": (
                "/proc/<pid>/smaps_rollup"
            ),
            "memory_pressure": (
                "/proc/pressure/memory"
            ),
            "backend_identity": (
                "DXVK log/HUD metadata or launch metadata"
            ),
        },
        "normalized_fixture": (
            fixture
        ),
        "synthetic_identifiability": {
            "episodes": EPISODES,
            "state_counts": counts,
            "fps_only": {
                "frame_threshold_ms": (
                    FPS_ONLY_THRESHOLD_MS
                ),
                "action_accuracy": (
                    fps_accuracy
                ),
                "gpu_bound_recall": (
                    fps_recall
                ),
                "gpu_downscale_false_positive_rate": (
                    fps_fpr
                ),
            },
            "multi_signal": {
                "action_accuracy": (
                    multi_accuracy
                ),
                "gpu_bound_recall": (
                    multi_recall
                ),
                "gpu_downscale_false_positive_rate": (
                    multi_fpr
                ),
            },
            "matched_recall": True,
        },
        "primary_findings": [
            "LOW_FPS_ALONE_DOES_NOT_IDENTIFY_THE_BOTTLENECK",
            "MULTI_SIGNAL_OBSERVATION_REDUCES_FALSE_GPU_DOWNSCALE_AT_MATCHED_GPU_BOUND_RECALL",
            "MEMAVAILABLE_PSI_AND_GPU_BUSY_HAVE_DIFFERENT_CONTROL_MEANINGS",
            "BACKEND_IDENTITY_MUST_BE_FROZEN_FOR_PROTON_COMPARISONS",
            "OBSERVATION_OVERHEAD_MUST_BE_MEASURED_BEFORE_LIVE_CONTROL",
        ],
        "claim_ceiling": (
            "READ_ONLY_SCHEMA_AND_SYNTHETIC_IDENTIFIABILITY_ONLY"
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
