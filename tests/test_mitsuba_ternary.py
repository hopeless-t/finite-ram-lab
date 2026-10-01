from __future__ import annotations

import pytest

from finite_ram_lab.mitsuba_ternary import (
    MITSUBA_MMPROJ_SHA256,
    PQ2_0,
    PRISM_RUNTIME_COMMIT,
    PTQ1_0,
    RuntimeIdentity,
    compare_packings,
    static_resident_budget,
)


def identity(**overrides):
    base = {
        "model_repo": "isichan-ai/Mitsuba-ComfyUI-27B-GGUF",
        "model_filename": "Mitsuba-ComfyUI-27B-v1.18-PQ2_0.gguf",
        "model_sha256": "a" * 64,
        "projector_filename": "mmproj-Q8_0.gguf",
        "projector_sha256": MITSUBA_MMPROJ_SHA256,
        "packing": "PQ2_0",
        "runtime_repo": "PrismML-Eng/llama.cpp",
        "runtime_commit": PRISM_RUNTIME_COMMIT,
        "runtime_binary_sha256": "b" * 64,
        "reasoning": "off",
        "cache_type_k": "q4_0",
        "cache_type_v": "q4_0",
        "context_size": 131072,
    }
    base.update(overrides)
    return RuntimeIdentity(**base)


def test_source_geometry_matches_prism_group_128_layouts():
    assert PQ2_0.block_bytes == 34
    assert PQ2_0.bits_per_weight == pytest.approx(2.125)
    assert PTQ1_0.block_bytes == 28
    assert PTQ1_0.bits_per_weight == pytest.approx(1.75)


def test_runtime_is_part_of_model_identity():
    a = identity(runtime_commit="1" * 40)
    b = identity(runtime_commit="2" * 40)
    assert a.model_sha256 == b.model_sha256
    assert a.identity_sha256 != b.identity_sha256


def test_reasoning_on_is_rejected_for_mitsuba_profile():
    with pytest.raises(ValueError, match="reasoning"):
        identity(reasoning="on").validate()


def test_budget_is_explicit_and_nonnegative():
    result = static_resident_budget(
        model_bytes=6_000_000_000,
        projector_bytes=629_000_000,
        kv_bytes=2_000_000_000,
    )
    assert result["total_bytes"] == 8_629_000_000
    with pytest.raises(ValueError):
        static_resident_budget(model_bytes=-1, projector_bytes=1)


def test_comparison_requires_same_weight_semantics():
    rows = [
        {
            "packing": "PQ2_0",
            "weights_semantics": "SAME_TERNARY_WEIGHTS",
            "peak_rss_bytes": 10,
        },
        {
            "packing": "PTQ1_0",
            "weights_semantics": "SAME_TERNARY_WEIGHTS",
            "peak_rss_bytes": 8,
        },
    ]
    result = compare_packings(rows)
    assert result["ptq1_minus_pq2_peak_rss_bytes"] == -2
    assert result["same_weights_control"] is True
