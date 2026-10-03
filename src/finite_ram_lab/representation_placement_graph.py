from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable


SCHEMA = "finite-ram-lab.representation-placement-graph/v0.1"


@dataclass(frozen=True)
class Representation:
    name: str
    size_ratio_vs_fp16: float
    quality_proxy: float
    decode_overhead_ms: float
    compatible_model_families: tuple[str, ...]
    kind: str


@dataclass(frozen=True)
class Placement:
    name: str
    base_latency_ms: float
    bandwidth_mib_per_s: float
    volatile_resident: bool
    local_storage_resident: bool
    network_required: bool


@dataclass(frozen=True)
class StateClass:
    name: str
    model_family: str
    fp16_mib: float
    deadline_ms: float
    quality_floor: float
    cloud_eligible: bool


REPRESENTATIONS = {
    "FP16": Representation(
        name="FP16",
        size_ratio_vs_fp16=1.0,
        quality_proxy=1.0,
        decode_overhead_ms=0.0,
        compatible_model_families=("CONVENTIONAL",),
        kind="WEIGHT_ENCODING",
    ),
    "AWQ4": Representation(
        name="AWQ4",
        size_ratio_vs_fp16=0.25,
        quality_proxy=0.985,
        decode_overhead_ms=1.5,
        compatible_model_families=("CONVENTIONAL",),
        kind="WEIGHT_ENCODING",
    ),
    "GPTQ4": Representation(
        name="GPTQ4",
        size_ratio_vs_fp16=0.25,
        quality_proxy=0.982,
        decode_overhead_ms=2.0,
        compatible_model_families=("CONVENTIONAL",),
        kind="WEIGHT_ENCODING",
    ),
    "NF4": Representation(
        name="NF4",
        size_ratio_vs_fp16=0.25,
        quality_proxy=0.980,
        decode_overhead_ms=4.0,
        compatible_model_families=("CONVENTIONAL",),
        kind="WEIGHT_ENCODING",
    ),
    "BITNET_B1_58": Representation(
        name="BITNET_B1_58",
        size_ratio_vs_fp16=1.58 / 16.0,
        quality_proxy=0.995,
        decode_overhead_ms=0.8,
        compatible_model_families=("BITNET_NATIVE",),
        kind="MODEL_NATIVE_ENCODING",
    ),
}


CONTAINERS = {
    "RAW": {
        "kind": "CONTAINER",
        "is_quantizer": False,
        "size_ratio": 1.0,
        "tensor_offsets": False,
    },
    "GGUF": {
        "kind": "CONTAINER",
        "is_quantizer": False,
        "size_ratio": 1.0,
        "tensor_offsets": True,
    },
}


PLACEMENTS = {
    "VRAM": Placement(
        name="VRAM",
        base_latency_ms=0.05,
        bandwidth_mib_per_s=100_000.0,
        volatile_resident=True,
        local_storage_resident=False,
        network_required=False,
    ),
    "RAM": Placement(
        name="RAM",
        base_latency_ms=0.10,
        bandwidth_mib_per_s=20_000.0,
        volatile_resident=True,
        local_storage_resident=False,
        network_required=False,
    ),
    "SSD": Placement(
        name="SSD",
        base_latency_ms=0.30,
        bandwidth_mib_per_s=3_000.0,
        volatile_resident=False,
        local_storage_resident=True,
        network_required=False,
    ),
    "CLOUD_OBJECT": Placement(
        name="CLOUD_OBJECT",
        base_latency_ms=35.0,
        bandwidth_mib_per_s=250.0,
        volatile_resident=False,
        local_storage_resident=False,
        network_required=True,
    ),
}


STATE_CLASSES = (
    StateClass(
        name="HOT_WEIGHT_SHARD",
        model_family="CONVENTIONAL",
        fp16_mib=512.0,
        deadline_ms=20.0,
        quality_floor=0.980,
        cloud_eligible=False,
    ),
    StateClass(
        name="WARM_EXPERT_SHARD",
        model_family="CONVENTIONAL",
        fp16_mib=512.0,
        deadline_ms=300.0,
        quality_floor=0.980,
        cloud_eligible=False,
    ),
    StateClass(
        name="COLD_MODEL_SHARD",
        model_family="CONVENTIONAL",
        fp16_mib=2048.0,
        deadline_ms=10_000.0,
        quality_floor=0.980,
        cloud_eligible=True,
    ),
    StateClass(
        name="BITNET_NATIVE_SHARD",
        model_family="BITNET_NATIVE",
        fp16_mib=2048.0,
        deadline_ms=1_000.0,
        quality_floor=0.990,
        cloud_eligible=False,
    ),
)


def encoded_mib(
    state: StateClass,
    representation: Representation,
) -> float:
    return (
        state.fp16_mib
        * representation.size_ratio_vs_fp16
    )


def fetch_latency_ms(
    state: StateClass,
    representation: Representation,
    placement: Placement,
) -> float:
    size_mib = encoded_mib(
        state,
        representation,
    )

    transfer_ms = (
        size_mib
        / placement.bandwidth_mib_per_s
        * 1000.0
    )

    return (
        placement.base_latency_ms
        + transfer_ms
        + representation.decode_overhead_ms
    )


def candidate(
    state: StateClass,
    representation: Representation,
    placement: Placement,
) -> dict:
    compatible = (
        state.model_family
        in representation.compatible_model_families
    )

    quality_ok = (
        representation.quality_proxy
        >= state.quality_floor
    )

    cloud_ok = (
        placement.name != "CLOUD_OBJECT"
        or state.cloud_eligible
    )

    latency_ms = fetch_latency_ms(
        state,
        representation,
        placement,
    )

    deadline_ok = (
        latency_ms <= state.deadline_ms
    )

    feasible = (
        compatible
        and quality_ok
        and cloud_ok
        and deadline_ok
    )

    size_mib = encoded_mib(
        state,
        representation,
    )

    return {
        "state_class": state.name,
        "representation": representation.name,
        "representation_kind": (
            representation.kind
        ),
        "placement": placement.name,
        "encoded_mib": size_mib,
        "quality_proxy": (
            representation.quality_proxy
        ),
        "latency_ms": latency_ms,
        "deadline_ms": state.deadline_ms,
        "compatible": compatible,
        "quality_ok": quality_ok,
        "cloud_ok": cloud_ok,
        "deadline_ok": deadline_ok,
        "feasible": feasible,
        "volatile_resident_mib": (
            size_mib
            if placement.volatile_resident
            else 0.0
        ),
        "local_storage_mib": (
            size_mib
            if placement.local_storage_resident
            else 0.0
        ),
        "network_fetch_mib": (
            size_mib
            if placement.network_required
            else 0.0
        ),
    }


def all_candidates(
    state: StateClass,
) -> list[dict]:
    return [
        candidate(
            state,
            representation,
            placement,
        )
        for representation
        in REPRESENTATIONS.values()
        for placement
        in PLACEMENTS.values()
    ]


def _objective_key(row: dict) -> tuple:
    return (
        row["volatile_resident_mib"],
        row["local_storage_mib"],
        row["network_fetch_mib"],
        -row["quality_proxy"],
        row["latency_ms"],
        row["representation"],
        row["placement"],
    )


def select_plan(
    state: StateClass,
) -> dict:
    feasible = [
        row
        for row in all_candidates(state)
        if row["feasible"]
    ]

    if not feasible:
        raise RuntimeError(
            f"no_feasible_plan:{state.name}"
        )

    return min(
        feasible,
        key=_objective_key,
    )


def force_cloud_plan(
    state: StateClass,
) -> dict:
    representation = REPRESENTATIONS["AWQ4"]
    placement = PLACEMENTS["CLOUD_OBJECT"]

    row = candidate(
        state,
        representation,
        placement,
    )

    # Diagnostic counterfactual: ignore policy-level
    # cloud eligibility but preserve compatibility,
    # quality, and the actual latency/deadline result.
    return {
        **row,
        "policy_override_cloud_eligibility": True,
        "counterfactual_deadline_success": (
            row["compatible"]
            and row["quality_ok"]
            and row["deadline_ok"]
        ),
    }


def bitnet_compatibility_probe() -> dict:
    conventional = next(
        state
        for state in STATE_CLASSES
        if state.name == "HOT_WEIGHT_SHARD"
    )

    row = candidate(
        conventional,
        REPRESENTATIONS["BITNET_B1_58"],
        PLACEMENTS["RAM"],
    )

    return {
        "attempted_model_family": (
            conventional.model_family
        ),
        "representation": "BITNET_B1_58",
        "compatible": row["compatible"],
        "feasible": row["feasible"],
        "reason": (
            "BITNET_IS_A_NATIVE_MODEL_ENCODING_NOT_A_RUNTIME_DEMOTION_FOR_ARBITRARY_CONVENTIONAL_WEIGHTS"
        ),
    }


def run_panel() -> dict:
    selected = {
        state.name: select_plan(state)
        for state in STATE_CLASSES
    }

    forced_cloud = {
        state.name: force_cloud_plan(state)
        for state in STATE_CLASSES
        if state.model_family == "CONVENTIONAL"
    }

    expected = {
        "HOT_WEIGHT_SHARD": (
            "AWQ4",
            "RAM",
        ),
        "WARM_EXPERT_SHARD": (
            "AWQ4",
            "SSD",
        ),
        "COLD_MODEL_SHARD": (
            "AWQ4",
            "CLOUD_OBJECT",
        ),
        "BITNET_NATIVE_SHARD": (
            "BITNET_B1_58",
            "SSD",
        ),
    }

    for state_name, pair in expected.items():
        row = selected[state_name]

        if (
            row["representation"],
            row["placement"],
        ) != pair:
            raise RuntimeError(
                f"selection_reference_changed:{state_name}"
            )

    if CONTAINERS["GGUF"]["is_quantizer"]:
        raise RuntimeError(
            "gguf_taxonomy_changed"
        )

    if (
        CONTAINERS["GGUF"]["size_ratio"]
        != 1.0
    ):
        raise RuntimeError(
            "gguf_must_not_be_modeled_as_compression"
        )

    bitnet_probe = (
        bitnet_compatibility_probe()
    )

    if bitnet_probe["compatible"]:
        raise RuntimeError(
            "bitnet_runtime_demotion_misclassified"
        )

    if forced_cloud[
        "HOT_WEIGHT_SHARD"
    ]["counterfactual_deadline_success"]:
        raise RuntimeError(
            "hot_cloud_unexpectedly_deadline_safe"
        )

    if forced_cloud[
        "WARM_EXPERT_SHARD"
    ]["counterfactual_deadline_success"]:
        raise RuntimeError(
            "warm_cloud_unexpectedly_deadline_safe"
        )

    if not forced_cloud[
        "COLD_MODEL_SHARD"
    ]["counterfactual_deadline_success"]:
        raise RuntimeError(
            "cold_cloud_unexpectedly_deadline_unsafe"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_REPRESENTATION_PLACEMENT_GRAPH_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "taxonomy": {
            "AWQ": "WEIGHT_QUANTIZATION_METHOD",
            "GPTQ": "WEIGHT_QUANTIZATION_METHOD",
            "NF4": "NUMERIC_REPRESENTATION",
            "GGUF": "CONTAINER",
            "BITNET_B1_58": (
                "MODEL_NATIVE_ENCODING_ARCHITECTURE"
            ),
        },
        "containers": CONTAINERS,
        "selected_plans": selected,
        "forced_cloud_counterfactual": (
            forced_cloud
        ),
        "bitnet_compatibility_probe": (
            bitnet_probe
        ),
        "primary_findings": [
            "REPRESENTATION_CHOICE_IS_NOT_PLACEMENT_CHOICE",
            "CONTAINER_IS_NOT_QUANTIZER",
            "BITNET_NATIVE_ENCODING_IS_NOT_ARBITRARY_RUNTIME_DEMOTION",
            "CLOUD_IS_A_DEADLINE_CLASS_NOT_A_UNIVERSAL_ESCAPE_HATCH",
            "PRECISION_AND_PLACEMENT_MUST_BE_OPTIMIZED_JOINTLY",
        ],
        "claim_ceiling": (
            "SYNTHETIC_REPRESENTATION_PLACEMENT_GRAPH_ONLY"
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
