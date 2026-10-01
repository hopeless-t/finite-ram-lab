from __future__ import annotations

from dataclasses import dataclass

from finite_ram_lab.frontier_compiler import TraceState


KV_BYTES_PER_CELL = {
    "fp16": 2048,
    "int8": 1056,
    "q4_0": 576,
    "k8v4": 816,
}


@dataclass(frozen=True)
class KvTierPlan:
    mode: str
    layers: int
    max_cells: int
    resident_cells: int
    full_vram_bytes: int
    gpu_resident_bytes: int
    host_authoritative_bytes: int
    freed_vram_bytes: int


@dataclass(frozen=True)
class ExpertTierPlan:
    logical_expert_bytes: int
    gpu_resident_bytes: int
    ram_complement_bytes: int
    file_fallback_bytes: int


@dataclass(frozen=True)
class BorrowPlan:
    cache_bytes: int
    borrowed_bytes: int
    prompt_scratch_bytes: int
    steady_peak_bytes: int
    prompt_peak_bytes: int
    temporary_expert_capacity_bytes: int


def kv_bytes_per_cell(mode: str) -> int:
    try:
        return KV_BYTES_PER_CELL[mode]
    except KeyError as exc:
        raise ValueError("kv_mode_invalid") from exc


def kv_tier_plan(
    *,
    mode: str,
    max_cells: int,
    resident_cells: int | None = None,
    layers: int = 1,
) -> KvTierPlan:
    if type(max_cells) is not int or max_cells < 1:
        raise ValueError("max_cells_invalid")
    if type(layers) is not int or layers < 1:
        raise ValueError("layers_invalid")

    if resident_cells is None:
        resident_cells = max_cells
    if type(resident_cells) is not int or not 1 <= resident_cells <= max_cells:
        raise ValueError("resident_cells_invalid")

    if mode == "k8v4" and resident_cells < max_cells:
        raise ValueError("k8v4_streaming_not_supported")

    cell = kv_bytes_per_cell(mode)
    full = max_cells * cell * layers
    gpu = resident_cells * cell * layers
    host = full if resident_cells < max_cells else 0

    return KvTierPlan(
        mode=mode,
        layers=layers,
        max_cells=max_cells,
        resident_cells=resident_cells,
        full_vram_bytes=full,
        gpu_resident_bytes=gpu,
        host_authoritative_bytes=host,
        freed_vram_bytes=full - gpu,
    )


def expert_complement_plan(
    *,
    logical_expert_bytes: int,
    gpu_resident_bytes: int,
    ram_budget_bytes: int | None = None,
) -> ExpertTierPlan:
    for name, value in (
        ("logical_expert_bytes", logical_expert_bytes),
        ("gpu_resident_bytes", gpu_resident_bytes),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name}_invalid")
    if gpu_resident_bytes > logical_expert_bytes:
        raise ValueError("gpu_exceeds_logical")

    complement = logical_expert_bytes - gpu_resident_bytes

    if ram_budget_bytes is None:
        ram = complement
    else:
        if type(ram_budget_bytes) is not int or ram_budget_bytes < 0:
            raise ValueError("ram_budget_bytes_invalid")
        ram = min(complement, ram_budget_bytes)

    return ExpertTierPlan(
        logical_expert_bytes=logical_expert_bytes,
        gpu_resident_bytes=gpu_resident_bytes,
        ram_complement_bytes=ram,
        file_fallback_bytes=complement - ram,
    )


def borrowed_cache_plan(
    *,
    cache_bytes: int,
    borrowed_bytes: int,
    prompt_scratch_bytes: int,
) -> BorrowPlan:
    for name, value in (
        ("cache_bytes", cache_bytes),
        ("borrowed_bytes", borrowed_bytes),
        ("prompt_scratch_bytes", prompt_scratch_bytes),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name}_invalid")
    if borrowed_bytes > cache_bytes:
        raise ValueError("borrow_exceeds_cache")
    if prompt_scratch_bytes > borrowed_bytes:
        raise ValueError("scratch_exceeds_borrow")

    # The source-backed design repurposes already allocated expert-cache slots.
    # Therefore prompt scratch does not add to the modeled cache allocation peak
    # when it fits in the borrowed region; it temporarily reduces expert capacity.
    return BorrowPlan(
        cache_bytes=cache_bytes,
        borrowed_bytes=borrowed_bytes,
        prompt_scratch_bytes=prompt_scratch_bytes,
        steady_peak_bytes=cache_bytes,
        prompt_peak_bytes=cache_bytes,
        temporary_expert_capacity_bytes=cache_bytes - borrowed_bytes,
    )


def ownership_partition_bytes(
    *,
    total_layers: int,
    owned_layers: int,
    per_layer_state_bytes: int,
    required_primary_state_bytes: int = 0,
) -> dict[str, int]:
    for name, value in (
        ("total_layers", total_layers),
        ("owned_layers", owned_layers),
        ("per_layer_state_bytes", per_layer_state_bytes),
        ("required_primary_state_bytes", required_primary_state_bytes),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name}_invalid")
    if total_layers < 1 or owned_layers > total_layers:
        raise ValueError("layer_range_invalid")

    old_full_copy = total_layers * per_layer_state_bytes
    carved = owned_layers * per_layer_state_bytes + required_primary_state_bytes
    return {
        "whole_model_copy_bytes": old_full_copy,
        "carved_state_bytes": carved,
        "avoided_duplicate_bytes": max(0, old_full_copy - carved),
    }


def idle_unload_byte_seconds(
    *,
    resident_bytes: int,
    horizon_seconds: float,
    active_seconds: float,
) -> dict[str, float]:
    if type(resident_bytes) is not int or resident_bytes < 0:
        raise ValueError("resident_bytes_invalid")
    if horizon_seconds <= 0 or active_seconds < 0 or active_seconds > horizon_seconds:
        raise ValueError("time_invalid")
    always_loaded = resident_bytes * horizon_seconds
    unloadable = resident_bytes * active_seconds
    return {
        "always_loaded_byte_seconds": float(always_loaded),
        "idle_unload_byte_seconds": float(unloadable),
        "saved_byte_seconds": float(always_loaded - unloadable),
    }


def strata_trace_states(
    *,
    kv_plan: KvTierPlan,
    expert_plan: ExpertTierPlan,
    session_state_bytes: int,
) -> tuple[TraceState, ...]:
    """Produce B428-compatible in-memory TraceState records.

    Semantic state is counted once. Tier mirrors/caches carry logical_bytes=0
    so replication is visible only in the physical frontier.

    File-backed expert bytes are intentionally excluded here: they are backing
    storage, not resident RAM/VRAM. OS page-cache residency must be observed
    separately rather than inferred from mapped file size.

    Time coordinates are normalized phases, not wall-clock measurements:
      [0,1): loaded/steady
      [1,2): prompt
      [2,3): decode
    """
    if type(session_state_bytes) is not int or session_state_bytes < 0:
        raise ValueError("session_state_bytes_invalid")

    states = [
        TraceState(
            "strata-kv-logical",
            0,
            3,
            logical_bytes=kv_plan.full_vram_bytes,
            encoded_bytes=0,
        ),
        TraceState(
            "strata-kv-gpu-resident",
            0,
            3,
            logical_bytes=0,
            encoded_bytes=kv_plan.gpu_resident_bytes,
        ),
        TraceState(
            "strata-expert-logical",
            0,
            3,
            logical_bytes=expert_plan.logical_expert_bytes,
            encoded_bytes=0,
        ),
        TraceState(
            "strata-expert-gpu-cache",
            0,
            3,
            logical_bytes=0,
            encoded_bytes=expert_plan.gpu_resident_bytes,
        ),
        TraceState(
            "strata-expert-ram-complement",
            0,
            3,
            logical_bytes=0,
            encoded_bytes=expert_plan.ram_complement_bytes,
        ),
        TraceState(
            "strata-session-state",
            0,
            3,
            logical_bytes=session_state_bytes,
            encoded_bytes=session_state_bytes,
        ),
    ]
    if kv_plan.host_authoritative_bytes:
        states.append(
            TraceState(
                "strata-kv-host-authoritative",
                0,
                3,
                logical_bytes=0,
                encoded_bytes=kv_plan.host_authoritative_bytes,
            )
        )
    return tuple(states)
