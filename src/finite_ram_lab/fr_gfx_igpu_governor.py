from __future__ import annotations

import hashlib
import json
from statistics import mean


SCHEMA = "finite-ram-lab.fr-gfx-001-happy-igpu-uma/v0.1"
SEED = "FR-GFX-001-v0.1"

FRAMES = 5000
TOTAL_UMA_MIB = 8192.0
GAME_CPU_MIB = 1100.0
TEXTURE_BASE_MIB = 2800.0
RENDER_TARGET_BASE_MIB = 520.0
UPSCALER_WORKING_SET_MIB = 81.0

FRAME_BUDGET_MS = 33.3
HEADROOM_SOFT_MIB = 700.0

SCALES = (1.0, 0.83, 0.67, 0.58)
TEXTURE_TIERS = (1.0, 0.75, 0.5)

CONFIGS = tuple(
    (scale, texture)
    for scale in SCALES
    for texture in TEXTURE_TIERS
)


def _u(
    frame: int,
    domain: str,
) -> float:
    value = int.from_bytes(
        hashlib.sha256(
            f"{SEED}|{domain}|{frame}".encode(
                "utf-8"
            )
        ).digest()[:8],
        "big",
    )

    return value / float(
        (1 << 64) - 1
    )


def _trace_frame(
    frame: int,
) -> tuple[
    float,
    float,
    float,
]:
    scene = (
        0.72
        + 0.55 * _u(
            frame,
            "scene",
        )
    )

    if (
        _u(
            frame,
            "spike",
        )
        < 0.08
    ):
        scene += (
            1.2
            + 1.0
            * _u(
                frame,
                "spike2",
            )
        )

    os_memory = (
        2500.0
        + 700.0
        * _u(
            frame,
            "os",
        )
    )

    if (
        _u(
            frame,
            "osspike",
        )
        < 0.06
    ):
        os_memory += (
            700.0
            + 700.0
            * _u(
                frame,
                "osspike2",
            )
        )

    cpu_bandwidth = (
        0.7
        + 0.6
        * _u(
            frame,
            "bw",
        )
    )

    if (
        _u(
            frame,
            "bwspike",
        )
        < 0.08
    ):
        cpu_bandwidth += 0.8

    return (
        scene,
        os_memory,
        cpu_bandwidth,
    )


def _evaluate(
    frame_state: tuple[
        float,
        float,
        float,
    ],
    config: tuple[
        float,
        float,
    ],
) -> dict:
    (
        scene,
        os_memory,
        cpu_bandwidth,
    ) = frame_state

    scale, texture = config

    gpu_memory = (
        TEXTURE_BASE_MIB
        * texture
        + RENDER_TARGET_BASE_MIB
        * scale
        * scale
        + (
            UPSCALER_WORKING_SET_MIB
            if scale < 1.0
            else 0.0
        )
    )

    headroom = (
        TOTAL_UMA_MIB
        - os_memory
        - GAME_CPU_MIB
        - gpu_memory
    )

    frame_ms = (
        8.0
        + scene
        * (
            13.0
            * scale
            * scale
            + 5.2
            * texture
        )
    )

    frame_ms += (
        max(
            0.0,
            cpu_bandwidth - 1.0,
        )
        * (
            2.4
            + 2.2
            * texture
        )
    )

    if (
        headroom
        < HEADROOM_SOFT_MIB
    ):
        frame_ms += (
            (
                HEADROOM_SOFT_MIB
                - headroom
            )
            / 100.0
            * 1.8
        )

    if headroom < 0.0:
        frame_ms += (
            20.0
            + (-headroom) / 80.0
        )

    quality = (
        0.62 * scale
        + 0.38 * texture
    )

    if scale < 1.0:
        quality += (
            0.12
            * (
                1.0 - scale
            )
        )

    quality = min(
        quality,
        1.0,
    )

    return {
        "frame_ms": frame_ms,
        "headroom_mib": headroom,
        "quality": quality,
        "gpu_memory_mib": (
            gpu_memory
        ),
    }


def _objective(
    frame_state,
    config,
) -> float:
    row = _evaluate(
        frame_state,
        config,
    )

    penalty = 0.0

    if (
        row["frame_ms"]
        > FRAME_BUDGET_MS
    ):
        penalty += (
            row["frame_ms"]
            - FRAME_BUDGET_MS
        ) * 5.0

    if (
        row["headroom_mib"]
        < 350.0
    ):
        penalty += (
            350.0
            - row[
                "headroom_mib"
            ]
        ) * 0.03

    if (
        row["quality"]
        < 0.66
    ):
        penalty += (
            0.66
            - row["quality"]
        ) * 120.0

    return (
        penalty
        + row["frame_ms"]
        * 0.25
        + (
            1.0
            - row["quality"]
        ) * 7.0
    )


def _neighbors(
    config: tuple[
        float,
        float,
    ],
) -> set[
    tuple[float, float]
]:
    scale, texture = config

    scale_index = (
        SCALES.index(
            scale
        )
    )

    texture_index = (
        TEXTURE_TIERS.index(
            texture
        )
    )

    output = {
        config,
    }

    for delta in (
        -1,
        1,
    ):
        candidate = (
            scale_index
            + delta
        )

        if (
            0
            <= candidate
            < len(SCALES)
        ):
            output.add(
                (
                    SCALES[
                        candidate
                    ],
                    texture,
                )
            )

    for delta in (
        -1,
        1,
    ):
        candidate = (
            texture_index
            + delta
        )

        if (
            0
            <= candidate
            < len(
                TEXTURE_TIERS
            )
        ):
            output.add(
                (
                    scale,
                    TEXTURE_TIERS[
                        candidate
                    ],
                )
            )

    return output


def _probe_config(
    frame: int,
    slot: int,
) -> tuple[
    float,
    float,
]:
    value = int.from_bytes(
        hashlib.sha256(
            (
                f"{SEED}|probe|"
                f"{frame}|{slot}"
            ).encode(
                "utf-8"
            )
        ).digest()[:8],
        "big",
    )

    return CONFIGS[
        value % len(CONFIGS)
    ]


def _quantile(
    values: list[float],
    q: float,
) -> float:
    ordered = sorted(
        values
    )

    index = round(
        q
        * (
            len(ordered) - 1
        )
    )

    return ordered[
        int(index)
    ]


def _summarize(
    rows: list[dict],
    *,
    evaluations: int,
    transitions: int,
) -> dict:
    frame_times = [
        row["frame_ms"]
        for row in rows
    ]

    headroom = [
        row["headroom_mib"]
        for row in rows
    ]

    quality = [
        row["quality"]
        for row in rows
    ]

    return {
        "mean_frame_ms": (
            mean(
                frame_times
            )
        ),
        "p95_frame_ms": (
            _quantile(
                frame_times,
                0.95,
            )
        ),
        "p99_frame_ms": (
            _quantile(
                frame_times,
                0.99,
            )
        ),
        "deadline_misses": sum(
            value
            > FRAME_BUDGET_MS
            for value
            in frame_times
        ),
        "memory_violations": sum(
            value < 0.0
            for value
            in headroom
        ),
        "minimum_headroom_mib": (
            min(
                headroom
            )
        ),
        "mean_quality": (
            mean(
                quality
            )
        ),
        "control_evaluations": (
            evaluations
        ),
        "transitions": (
            transitions
        ),
    }


def _run_static(
    config: tuple[
        float,
        float,
    ],
) -> dict:
    rows = []

    for frame in range(
        FRAMES
    ):
        evaluated = _evaluate(
            _trace_frame(
                frame
            ),
            config,
        )

        rows.append(
            evaluated
        )

    return _summarize(
        rows,
        evaluations=FRAMES,
        transitions=0,
    )


def _run_full_expert() -> dict:
    rows = []
    previous = None
    transitions = 0

    for frame in range(
        FRAMES
    ):
        frame_state = (
            _trace_frame(
                frame
            )
        )

        config = min(
            CONFIGS,
            key=lambda candidate: (
                _objective(
                    frame_state,
                    candidate,
                )
            ),
        )

        if (
            previous is not None
            and config
            != previous
        ):
            transitions += 1

        previous = config

        rows.append(
            _evaluate(
                frame_state,
                config,
            )
        )

    return _summarize(
        rows,
        evaluations=(
            FRAMES
            * len(CONFIGS)
        ),
        transitions=(
            transitions
        ),
    )


def _run_bounded(
    global_probes: int,
) -> dict:
    config = (
        1.0,
        1.0,
    )

    rows = []
    transitions = 0
    evaluations = 0
    stable = 0

    for frame in range(
        FRAMES
    ):
        frame_state = (
            _trace_frame(
                frame
            )
        )

        current = _evaluate(
            frame_state,
            config,
        )

        evaluations += 1

        risk = (
            current[
                "frame_ms"
            ] > 30.5
            or current[
                "headroom_mib"
            ] < 550.0
        )

        upgrade = False

        if (
            not risk
            and current[
                "quality"
            ] < 0.9
            and current[
                "frame_ms"
            ] < 24.5
            and current[
                "headroom_mib"
            ] > 900.0
        ):
            stable += 1

            if stable >= 8:
                upgrade = True
                stable = 0
        elif risk:
            stable = 0

        next_config = config

        if risk or upgrade:
            local = _neighbors(
                config
            )

            evaluations += (
                len(local) - 1
            )

            best_local = min(
                local,
                key=lambda candidate: (
                    _objective(
                        frame_state,
                        candidate,
                    )
                ),
            )

            local_row = _evaluate(
                frame_state,
                best_local,
            )

            next_config = (
                best_local
            )

            need_probe = (
                (
                    local_row[
                        "frame_ms"
                    ]
                    > FRAME_BUDGET_MS
                )
                or (
                    local_row[
                        "headroom_mib"
                    ]
                    < 350.0
                )
                or (
                    upgrade
                    and best_local
                    == config
                )
            )

            if (
                global_probes
                and need_probe
            ):
                candidates = set(
                    local
                )

                for slot in range(
                    global_probes
                ):
                    candidates.add(
                        _probe_config(
                            frame,
                            slot,
                        )
                    )

                evaluations += (
                    len(
                        candidates
                        - local
                    )
                )

                next_config = min(
                    candidates,
                    key=lambda candidate: (
                        _objective(
                            frame_state,
                            candidate,
                        )
                    ),
                )

        if (
            next_config
            != config
        ):
            transitions += 1

        config = next_config

        rows.append(
            _evaluate(
                frame_state,
                config,
            )
        )

    return _summarize(
        rows,
        evaluations=(
            evaluations
        ),
        transitions=(
            transitions
        ),
    )


def run_panel() -> dict:
    policies = {
        "NATIVE_STATIC": (
            _run_static(
                (
                    1.0,
                    1.0,
                )
            )
        ),
        "UPSCALE_STATIC": (
            _run_static(
                (
                    0.67,
                    0.75,
                )
            )
        ),
        "EXPERT_FULL_SCAN": (
            _run_full_expert()
        ),
        "LOCAL_ONLY": (
            _run_bounded(0)
        ),
        "BOUNDED_PROBE_4": (
            _run_bounded(4)
        ),
    }

    frozen = {
        "NATIVE_STATIC": (
            706,
            185,
            5000,
        ),
        "UPSCALE_STATIC": (
            224,
            0,
            5000,
        ),
        "EXPERT_FULL_SCAN": (
            41,
            0,
            60000,
        ),
        "LOCAL_ONLY": (
            69,
            0,
            6970,
        ),
        "BOUNDED_PROBE_4": (
            53,
            0,
            7379,
        ),
    }

    for policy, expected in (
        frozen.items()
    ):
        row = policies[
            policy
        ]

        actual = (
            row[
                "deadline_misses"
            ],
            row[
                "memory_violations"
            ],
            row[
                "control_evaluations"
            ],
        )

        if actual != expected:
            raise RuntimeError(
                (
                    "frozen_result_changed:"
                    f"{policy}:{actual}"
                )
            )

    local = policies[
        "LOCAL_ONLY"
    ]

    bounded = policies[
        "BOUNDED_PROBE_4"
    ]

    expert = policies[
        "EXPERT_FULL_SCAN"
    ]

    if (
        bounded[
            "deadline_misses"
        ]
        >= local[
            "deadline_misses"
        ]
    ):
        raise RuntimeError(
            "bounded_probe_tail_not_better"
        )

    if (
        bounded[
            "control_evaluations"
        ]
        >= expert[
            "control_evaluations"
        ]
    ):
        raise RuntimeError(
            "bounded_probe_not_cheaper_than_full_scan"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_UMA_IGPU_GOVERNOR_VALIDATED"
        ),
        "synthetic_only": True,
        "live_game_claim": False,
        "frame_budget_ms": (
            FRAME_BUDGET_MS
        ),
        "uma_budget_mib": (
            TOTAL_UMA_MIB
        ),
        "policies": policies,
        "derived": {
            "bounded_probe_deadline_reduction_vs_local_only": (
                1.0
                - bounded[
                    "deadline_misses"
                ]
                / local[
                    "deadline_misses"
                ]
            ),
            "bounded_probe_control_increase_vs_local_only": (
                bounded[
                    "control_evaluations"
                ]
                / local[
                    "control_evaluations"
                ]
                - 1.0
            ),
            "bounded_probe_control_reduction_vs_full_scan": (
                1.0
                - bounded[
                    "control_evaluations"
                ]
                / expert[
                    "control_evaluations"
                ]
            ),
            "bounded_probe_quality_delta_vs_local_only": (
                bounded[
                    "mean_quality"
                ]
                - local[
                    "mean_quality"
                ]
            ),
            "bounded_probe_min_headroom_gain_mib_vs_local_only": (
                bounded[
                    "minimum_headroom_mib"
                ]
                - local[
                    "minimum_headroom_mib"
                ]
            ),
        },
        "source_grounding": {
            "linux_drm_uma": (
                "Linux DRM memory management supports UMA and dedicated-VRAM devices."
            ),
            "vulkan_sparse": (
                "Vulkan sparse residency can keep only selected image/buffer regions resident when hardware supports it."
            ),
            "fsr_dynamic_resolution": (
                "FSR-class upscaling and dynamic resolution motivate quality/working-set tradeoffs; the 81 MiB figure here is a synthetic pinned reference from a published 1080p working-set example, not a universal constant."
            ),
        },
        "primary_findings": [
            "NATIVE_QUALITY_CAN_VIOLATE_SHARED_UMA_HEADROOM",
            "STATIC_UPSCALING_CAN_REMOVE_MEMORY_VIOLATIONS_BUT_LEAVE_TAIL_MISSES",
            "FULL_EXPERT_SCAN_BUYS_BETTER_QUALITY_AND_TAIL_AT_HIGH_CONTROL_COST",
            "BOUNDED_GLOBAL_PROBES_CAN_REDUCE_LOCAL_CONTROLLER_TAIL_MISSES_WITH_SMALL_EXTRA_CONTROL_WORK",
            "IGPU_CONTROL_MUST_PRICE_FRAME_TIME_QUALITY_AND_SHARED_MEMORY_TOGETHER",
        ],
        "claim_ceiling": (
            "SYNTHETIC_UMA_IGPU_GOVERNOR_ONLY"
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
