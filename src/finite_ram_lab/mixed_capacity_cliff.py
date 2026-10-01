from __future__ import annotations

from itertools import product
from typing import Iterable, Sequence

from finite_ram_lab.bounded_frontier_controller import (
    StateOption,
    aggregate_options,
    exact_pareto_controller,
    option_is_safe,
)
from finite_ram_lab.pareto_beam_controller import (
    beam_pareto_controller,
    frontier_recovery_metrics,
)


MIB = 1 << 20

# B432 source-backed INT8 KV pool sizes for:
# 12 QSA layers, max_cells=131072, resident_cells=32768.
STRATA_INT8_KV_FULL_MIB = 1584
STRATA_INT8_KV_RESIDENT_MIB = 396
STRATA_INT8_KV_HOST_MIB = 1584

# docs/DETAILS.md describes the Q2_0 expert set as approximately 34 GB.
# For this mixed scenario only, treat 34 GiB as a normalized source-anchored
# logical expert volume so tier partitions sum to one stable value.
EXPERT_LOGICAL_PROXY_MIB = 34 * 1024

# Public 2026-09-30 community log: prompt borrows 4.62 GiB of expert-cache
# slots. It is rounded upstream, so the nearest-MiB conversion remains an
# approximate source anchor rather than an exact allocation size.
PROMPT_BORROW_PROXY_MIB = round(4.62 * 1024)


def _option(
    state: str,
    name: str,
    *,
    vram: int = 0,
    ram: int = 0,
    vram_area: float = 0.0,
    ram_area: float = 0.0,
    traffic: float = 0.0,
    compute: float = 0.0,
    latency: float = 0.0,
    error: float = 0.0,
    release: bool = False,
    release_proven: bool = False,
) -> StateOption:
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(("RAM", ram_area), ("VRAM", vram_area)),
        traffic_bytes=traffic,
        compute_cost=compute,
        latency_cost=latency,
        error_cost=error,
        releases_semantic_state=release,
        release_proven=release_proven,
    )


def mixed_option_groups() -> tuple[tuple[StateOption, ...], ...]:
    """Source-anchored mixed controller scenario.

    Memory coordinates are MiB-equivalent units.

    Source-backed/static anchors:
    - Strata INT8 KV pool sizes from B432;
    - Strata expert placement mechanisms and ~34-GB expert volume;
    - 4.62-GiB prompt cache borrowing observation.

    Explicitly normalized components:
    - traffic/compute/latency costs;
    - FlashAttention-pattern semantic reduction footprint;
    - GEMMul8-pattern temporalization footprint;
    - idle-unload byte-second proxy.

    This is a controller stress scenario, not one executable application.
    """
    kv = (
        _option(
            "strata_kv",
            "full_int8_vram",
            vram=STRATA_INT8_KV_FULL_MIB,
            vram_area=STRATA_INT8_KV_FULL_MIB * 3,
        ),
        _option(
            "strata_kv",
            "stream_int8",
            vram=STRATA_INT8_KV_RESIDENT_MIB,
            ram=STRATA_INT8_KV_HOST_MIB,
            vram_area=STRATA_INT8_KV_RESIDENT_MIB * 3,
            ram_area=STRATA_INT8_KV_HOST_MIB * 3,
            traffic=6,
            latency=2,
        ),
    )

    experts = (
        _option(
            "strata_experts",
            "gpu20_ram14",
            vram=20 * 1024,
            ram=14 * 1024,
            vram_area=20 * 1024 * 3,
            ram_area=14 * 1024 * 3,
            traffic=1,
            latency=1,
        ),
        _option(
            "strata_experts",
            "gpu12_ram22",
            vram=12 * 1024,
            ram=22 * 1024,
            vram_area=12 * 1024 * 3,
            ram_area=22 * 1024 * 3,
            traffic=4,
            latency=3,
        ),
        _option(
            "strata_experts",
            "gpu8_ram26",
            vram=8 * 1024,
            ram=26 * 1024,
            vram_area=8 * 1024 * 3,
            ram_area=26 * 1024 * 3,
            traffic=7,
            latency=5,
        ),
        _option(
            "strata_experts",
            "gpu8_ram8_file_backing",
            vram=8 * 1024,
            ram=8 * 1024,
            vram_area=8 * 1024 * 3,
            ram_area=8 * 1024 * 3,
            traffic=20,
            latency=12,
        ),
    )

    prefill = (
        _option(
            "strata_prefill",
            "dedicated_prompt_scratch",
            vram=PROMPT_BORROW_PROXY_MIB,
            vram_area=PROMPT_BORROW_PROXY_MIB,
        ),
        _option(
            "strata_prefill",
            "borrow_expert_cache",
            traffic=3,
            latency=1,
        ),
    )

    semantic_reduction = (
        _option(
            "semantic_reduction",
            "materialize",
            vram=1024,
            vram_area=1024 * 3,
        ),
        _option(
            "semantic_reduction",
            "future_sufficient_summary",
            vram=256,
            vram_area=256 * 3,
            compute=2,
            release=True,
            release_proven=True,
        ),
    )

    temporalization = (
        _option(
            "temporalization",
            "wide_frontier",
            vram=2048,
            vram_area=2048 * 3,
        ),
        _option(
            "temporalization",
            "blocked_frontier",
            vram=512,
            vram_area=512 * 3,
            traffic=6,
            compute=4,
            latency=1,
        ),
    )

    idle_lifetime = (
        _option(
            "idle_lifetime",
            "always_loaded",
            vram_area=1024 * 10,
            ram_area=2048 * 10,
        ),
        _option(
            "idle_lifetime",
            "idle_unload",
            vram_area=1024 * 4,
            ram_area=2048 * 4,
            traffic=4,
            latency=3,
        ),
    )

    return (
        kv,
        experts,
        prefill,
        semantic_reduction,
        temporalization,
        idle_lifetime,
    )


def minimum_vram_for_ram(ram_capacity_mib: int) -> int | None:
    if type(ram_capacity_mib) is not int or ram_capacity_mib < 0:
        raise ValueError("ram_capacity_invalid")

    candidates = []
    for selection in product(*mixed_option_groups()):
        if not all(option_is_safe(option) for option in selection):
            continue
        plan = aggregate_options(selection)
        resident = dict(plan.resident_by_tier)
        if resident.get("RAM", 0) <= ram_capacity_mib:
            candidates.append(resident.get("VRAM", 0))

    return min(candidates) if candidates else None


def frontier_option_sets(plans) -> dict[str, list[str]]:
    out: dict[str, set[str]] = {}
    for plan in plans:
        for state, option in plan.choices:
            out.setdefault(state, set()).add(option)
    return {
        state: sorted(options)
        for state, options in sorted(out.items())
    }


def capacity_sweep(
    *,
    vram_capacities_mib: Sequence[int],
    ram_capacities_mib: Sequence[int],
    beam_width: int = 64,
) -> list[dict[str, object]]:
    groups = mixed_option_groups()
    rows = []

    for ram in ram_capacities_mib:
        for vram in vram_capacities_mib:
            capacities = {"RAM": int(ram), "VRAM": int(vram)}
            exact = exact_pareto_controller(groups, capacities)
            approximate = beam_pareto_controller(
                groups,
                capacities,
                beam_width=beam_width,
            )

            if exact:
                metrics = frontier_recovery_metrics(
                    approximate,
                    exact,
                    ("RAM", "VRAM"),
                )
            else:
                metrics = {
                    "exact_frontier_points": 0,
                    "approx_frontier_points": len(approximate),
                    "recovered_exact_points": 0,
                    "exact_point_coverage": 1.0 if not approximate else 0.0,
                    "approx_points_dominated_by_exact": 0,
                    "approx_dominated_fraction": 0.0,
                    "mean_domination_gap": 0.0,
                    "max_domination_gap": 0.0,
                }

            rows.append(
                {
                    "RAM_mib": ram,
                    "VRAM_mib": vram,
                    "feasible": bool(exact),
                    "exact_frontier_points": len(exact),
                    "beam_frontier_points": len(approximate),
                    "beam_exact_point_coverage": metrics["exact_point_coverage"],
                    "beam_dominated_fraction": metrics["approx_dominated_fraction"],
                    "exact_option_sets": frontier_option_sets(exact),
                }
            )

    return rows
