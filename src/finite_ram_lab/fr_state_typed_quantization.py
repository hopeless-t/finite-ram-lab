from __future__ import annotations

import json


SCHEMA = "finite-ram-lab.fr-quant-002-state-typed-quantization/v0.1"


def grouped_effective_bits(
    *,
    payload_bits: float,
    group_size: int,
    scale_bits: int,
    zero_bits: int = 0,
) -> float:
    if group_size <= 0:
        raise ValueError(
            "group_size_must_be_positive"
        )

    return (
        payload_bits
        + (
            scale_bits
            + zero_bits
        ) / group_size
    )


def sparse_outlier_effective_bits(
    *,
    bulk_bits: float,
    outlier_fraction: float,
    outlier_value_bits: int,
    outlier_index_bits: int,
) -> float:
    if not (
        0.0
        <= outlier_fraction
        <= 1.0
    ):
        raise ValueError(
            "outlier_fraction_invalid"
        )

    return (
        (
            1.0
            - outlier_fraction
        )
        * bulk_bits
        + outlier_fraction
        * (
            outlier_value_bits
            + outlier_index_bits
        )
    )


def kv_cache_mib(
    *,
    layers: int,
    tokens: int,
    kv_heads: int,
    head_dim: int,
    effective_bits: float,
    batch: int = 1,
) -> float:
    elements = (
        2
        * layers
        * tokens
        * kv_heads
        * head_dim
        * batch
    )

    bytes_total = (
        elements
        * effective_bits
        / 8.0
    )

    return (
        bytes_total
        / 1024.0
        / 1024.0
    )


def activation_buffer_mib(
    *,
    batch: int,
    tokens: int,
    hidden: int,
    effective_bits: float,
) -> float:
    elements = (
        batch
        * tokens
        * hidden
    )

    return (
        elements
        * effective_bits
        / 8.0
        / 1024.0
        / 1024.0
    )


WEIGHT_CANDIDATES = (
    {
        "name": "FP16",
        "effective_bits": 16.0,
        "quality_proxy": 1.000,
        "class": "BASELINE",
    },
    {
        "name": "AWQ4_G128",
        "effective_bits": 4.25,
        "quality_proxy": 0.985,
        "class": "WEIGHT_PTQ",
    },
    {
        "name": "GPTQ4_G128",
        "effective_bits": 4.25,
        "quality_proxy": 0.982,
        "class": "WEIGHT_PTQ",
    },
    {
        "name": "NF4_DOUBLE_QUANT_G128",
        "effective_bits": 4.125,
        "quality_proxy": 0.980,
        "class": "WEIGHT_NUMERIC_PLUS_METADATA_QUANT",
    },
    {
        "name": "SPQR3_OUTLIER_0_5PCT",
        "effective_bits": 3.145,
        "quality_proxy": 0.990,
        "class": "SPARSE_OUTLIER_ESCAPE",
    },
    {
        "name": "AQLM_2_5",
        "effective_bits": 2.75,
        "quality_proxy": 0.965,
        "class": "ADDITIVE_CODEBOOK",
    },
    {
        "name": "QUIP_SHARP_2",
        "effective_bits": 2.25,
        "quality_proxy": 0.970,
        "class": "LATTICE_CODEBOOK",
    },
)


ACTIVATION_CANDIDATES = (
    {
        "name": "FP16_ACT",
        "effective_bits": 16.0,
        "quality_proxy": 1.000,
    },
    {
        "name": "SMOOTHQUANT_W8A8_ACT",
        "effective_bits": 8.0,
        "quality_proxy": 0.995,
    },
    {
        "name": "FP8_ACT",
        "effective_bits": 8.0,
        "quality_proxy": 0.992,
    },
)


KV_CANDIDATES = (
    {
        "name": "FP16_KV",
        "effective_bits": 16.0,
        "quality_proxy": 1.000,
    },
    {
        "name": "Q8_KV",
        "effective_bits": 8.25,
        "quality_proxy": 0.999,
    },
    {
        "name": "KIVI2_EFFECTIVE",
        "effective_bits": 2.5,
        "quality_proxy": 0.985,
    },
)


def _select(
    candidates,
    *,
    quality_floor: float,
) -> dict:
    eligible = [
        row
        for row in candidates
        if row[
            "quality_proxy"
        ] >= quality_floor
    ]

    if not eligible:
        raise RuntimeError(
            "no_candidate_meets_quality_floor"
        )

    return min(
        eligible,
        key=lambda row: (
            row[
                "effective_bits"
            ],
            -row[
                "quality_proxy"
            ],
            row["name"],
        ),
    )


def run_panel() -> dict:
    grouped = {
        "q4_g32_scale16_zero16": (
            grouped_effective_bits(
                payload_bits=4.0,
                group_size=32,
                scale_bits=16,
                zero_bits=16,
            )
        ),
        "q4_g128_scale16_zero16": (
            grouped_effective_bits(
                payload_bits=4.0,
                group_size=128,
                scale_bits=16,
                zero_bits=16,
            )
        ),
        "q4_g32_double_quant_meta": (
            grouped_effective_bits(
                payload_bits=4.0,
                group_size=32,
                scale_bits=8,
                zero_bits=8,
            )
        ),
        "q4_g128_double_quant_meta": (
            grouped_effective_bits(
                payload_bits=4.0,
                group_size=128,
                scale_bits=8,
                zero_bits=8,
            )
        ),
    }

    spqr = (
        sparse_outlier_effective_bits(
            bulk_bits=3.0,
            outlier_fraction=0.005,
            outlier_value_bits=16,
            outlier_index_bits=16,
        )
    )

    kv_fp16 = kv_cache_mib(
        layers=32,
        tokens=32768,
        kv_heads=8,
        head_dim=128,
        effective_bits=16.0,
    )

    kv_2_5 = kv_cache_mib(
        layers=32,
        tokens=32768,
        kv_heads=8,
        head_dim=128,
        effective_bits=2.5,
    )

    act_fp16 = (
        activation_buffer_mib(
            batch=1,
            tokens=4096,
            hidden=4096,
            effective_bits=16.0,
        )
    )

    act_int8 = (
        activation_buffer_mib(
            batch=1,
            tokens=4096,
            hidden=4096,
            effective_bits=8.0,
        )
    )

    selected = {
        "weight_quality_0_98": (
            _select(
                WEIGHT_CANDIDATES,
                quality_floor=0.98,
            )
        ),
        "weight_quality_0_97": (
            _select(
                WEIGHT_CANDIDATES,
                quality_floor=0.97,
            )
        ),
        "activation_quality_0_99": (
            _select(
                ACTIVATION_CANDIDATES,
                quality_floor=0.99,
            )
        ),
        "kv_quality_0_98": (
            _select(
                KV_CANDIDATES,
                quality_floor=0.98,
            )
        ),
    }

    frozen = {
        "grouped": {
            "q4_g32_scale16_zero16": 5.0,
            "q4_g128_scale16_zero16": 4.25,
            "q4_g32_double_quant_meta": 4.5,
            "q4_g128_double_quant_meta": 4.125,
        },
        "spqr": 3.145,
        "kv_fp16": 4096.0,
        "kv_2_5": 640.0,
        "act_fp16": 32.0,
        "act_int8": 16.0,
        "selected": {
            "weight_quality_0_98": (
                "SPQR3_OUTLIER_0_5PCT"
            ),
            "weight_quality_0_97": (
                "QUIP_SHARP_2"
            ),
            "activation_quality_0_99": (
                "SMOOTHQUANT_W8A8_ACT"
            ),
            "kv_quality_0_98": (
                "KIVI2_EFFECTIVE"
            ),
        },
    }

    actual_selected = {
        key: row["name"]
        for key, row
        in selected.items()
    }

    if grouped != frozen[
        "grouped"
    ]:
        raise RuntimeError(
            "group_metadata_surface_changed"
        )

    if spqr != frozen["spqr"]:
        raise RuntimeError(
            "spqr_effective_bits_changed"
        )

    if kv_fp16 != frozen[
        "kv_fp16"
    ]:
        raise RuntimeError(
            "kv_fp16_geometry_changed"
        )

    if kv_2_5 != frozen[
        "kv_2_5"
    ]:
        raise RuntimeError(
            "kv_quant_geometry_changed"
        )

    if act_fp16 != frozen[
        "act_fp16"
    ]:
        raise RuntimeError(
            "activation_fp16_changed"
        )

    if act_int8 != frozen[
        "act_int8"
    ]:
        raise RuntimeError(
            "activation_int8_changed"
        )

    if actual_selected != frozen[
        "selected"
    ]:
        raise RuntimeError(
            "synthetic_selection_changed:"
            f"{actual_selected}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "STATE_TYPED_QUANTIZATION_ACCOUNTING_VALIDATED"
        ),
        "group_metadata_effective_bits": (
            grouped
        ),
        "outlier_escape_effective_bits": {
            "spqr_like_3bit_plus_0_5pct_fp16_indexed_outliers": (
                spqr
            ),
        },
        "kv_geometry": {
            "fixture": {
                "layers": 32,
                "tokens": 32768,
                "kv_heads": 8,
                "head_dim": 128,
                "batch": 1,
            },
            "fp16_mib": (
                kv_fp16
            ),
            "effective_2_5bit_mib": (
                kv_2_5
            ),
            "reduction_fraction": (
                1.0
                - kv_2_5
                / kv_fp16
            ),
        },
        "activation_geometry": {
            "fixture": {
                "batch": 1,
                "tokens": 4096,
                "hidden": 4096,
            },
            "fp16_buffer_mib": (
                act_fp16
            ),
            "int8_or_fp8_buffer_mib": (
                act_int8
            ),
        },
        "synthetic_candidates": {
            "weights": list(
                WEIGHT_CANDIDATES
            ),
            "activations": list(
                ACTIVATION_CANDIDATES
            ),
            "kv": list(
                KV_CANDIDATES
            ),
        },
        "synthetic_selections": (
            selected
        ),
        "source_boundaries": {
            "quality_proxies": (
                "Synthetic controls only; not cross-method benchmark measurements."
            ),
            "effective_bits": (
                "Accounting examples include explicit metadata assumptions and are not universal file-format sizes."
            ),
            "GGUF": (
                "Container/metadata axis only; not a quantizer."
            ),
            "BitNet": (
                "Native architecture/model encoding; not a runtime demotion candidate for arbitrary models."
            ),
        },
        "primary_findings": [
            "QUANTIZATION_MUST_BE_TYPED_BY_STATE_CLASS",
            "FOUR_BIT_PAYLOAD_DOES_NOT_IMPLY_FOUR_EFFECTIVE_BITS",
            "QUANTIZATION_METADATA_CAN_BE_MATERIAL_AT_SMALL_GROUP_SIZES",
            "OUTLIER_ESCAPE_IS_A_SEPARATE_REPRESENTATION_ATOM",
            "KV_CACHE_CAN_DOMINATE_LONG_CONTEXT_MEMORY_EVEN_AFTER_WEIGHT_QUANTIZATION",
            "ACTIVATION_QUANTIZATION_TARGETS_A_DIFFERENT_PEAK_THAN_WEIGHT_QUANTIZATION",
            "DYNAMIC_MIXED_PRECISION_SHOULD_OPTIMIZE_EFFECTIVE_BITS_NOT_LABEL_BITWIDTH",
        ],
        "claim_ceiling": (
            "SOURCE_GROUNDED_FORMULA_AND_SYNTHETIC_STATE_TYPED_QUANTIZATION_ONLY"
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
