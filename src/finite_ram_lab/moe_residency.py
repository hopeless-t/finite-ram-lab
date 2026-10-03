from __future__ import annotations

import json
from dataclasses import dataclass

MIB = 1024 * 1024


@dataclass(frozen=True)
class MoEGeometry:
    name: str = "ELYZA-Thinking-1.0-llm-jp-4-32b-a3b"
    layers: int = 32
    hidden_size: int = 2560
    moe_intermediate_size: int = 960
    experts_per_layer: int = 128
    active_experts_per_token: int = 8
    total_params: int = 32_139_028_992
    active_params: int = 3_827_476_992
    embedding_params: int = 503_316_480
    dtype_bytes: int = 2

    @property
    def expert_params(self) -> int:
        # Qwen3-MoE expert MLP: gate + up + down projections.
        return 3 * self.hidden_size * self.moe_intermediate_size

    @property
    def all_expert_params(self) -> int:
        return self.expert_params * self.experts_per_layer * self.layers

    @property
    def shared_params(self) -> int:
        return self.total_params - self.all_expert_params

    @property
    def active_expert_params(self) -> int:
        return self.expert_params * self.active_experts_per_token * self.layers

    @property
    def derived_active_params(self) -> int:
        return self.shared_params + self.active_expert_params

    def validate(self) -> None:
        if self.derived_active_params != self.active_params:
            raise ValueError(
                f"derived active params {self.derived_active_params} != published {self.active_params}"
            )


def params_to_mib(params: float, dtype_bytes: int = 2) -> float:
    return params * dtype_bytes / MIB


def uniform_expected_distinct_experts(
    tokens: int, geometry: MoEGeometry | None = None
) -> float:
    """Expected expert union per layer under independent uniform top-k routing."""
    if tokens < 0:
        raise ValueError("tokens must be non-negative")
    g = geometry or MoEGeometry()
    if tokens == 0:
        return 0.0
    miss_one_token = 1.0 - g.active_experts_per_token / g.experts_per_layer
    return g.experts_per_layer * (1.0 - miss_one_token**tokens)


def top_cache_mass(experts: int, cache_slots: int, alpha: float) -> float:
    """Static hot-set mass under a Zipf popularity shadow model."""
    if experts <= 0:
        raise ValueError("experts must be positive")
    if not 0 <= cache_slots <= experts:
        raise ValueError("cache_slots must be in [0, experts]")
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    if cache_slots == 0:
        return 0.0
    if cache_slots == experts:
        return 1.0

    weights = [1.0 if alpha == 0 else rank ** (-alpha) for rank in range(1, experts + 1)]
    return sum(weights[:cache_slots]) / sum(weights)


def evaluate(
    cache_slots_per_layer: int,
    routing_alpha: float,
    io_bandwidth_mib_s: float,
    runtime_kv_reserve_mib: float = 768.0,
    geometry: MoEGeometry | None = None,
) -> dict[str, float | int | str | None]:
    g = geometry or MoEGeometry()
    g.validate()

    if cache_slots_per_layer < g.active_experts_per_token:
        raise ValueError("cache must hold at least one token's active experts per layer")
    if cache_slots_per_layer > g.experts_per_layer:
        raise ValueError("cache exceeds expert count")
    if io_bandwidth_mib_s <= 0:
        raise ValueError("io bandwidth must be positive")

    hit_mass = top_cache_mass(
        g.experts_per_layer, cache_slots_per_layer, routing_alpha
    )
    expected_misses_per_layer = g.active_experts_per_token * (1.0 - hit_mass)
    streamed_params_per_token = (
        expected_misses_per_layer * g.expert_params * g.layers
    )
    stream_mib_per_token = params_to_mib(streamed_params_per_token, g.dtype_bytes)

    resident_params = (
        g.shared_params
        + cache_slots_per_layer * g.expert_params * g.layers
    )
    resident_mib = (
        params_to_mib(resident_params, g.dtype_bytes) + runtime_kv_reserve_mib
    )

    return {
        "cache_slots_per_layer": cache_slots_per_layer,
        "routing_alpha": routing_alpha,
        "io_bandwidth_mib_s": io_bandwidth_mib_s,
        "hotset_hit_mass": round(hit_mass, 9),
        "expected_misses_per_layer": round(expected_misses_per_layer, 9),
        "stream_mib_per_token_bf16": round(stream_mib_per_token, 6),
        "io_bound_tokens_per_s": (
            None
            if stream_mib_per_token == 0
            else round(io_bandwidth_mib_s / stream_mib_per_token, 6)
        ),
        "resident_mib_bf16_plus_reserve": round(resident_mib, 3),
        "resident_gib_bf16_plus_reserve": round(resident_mib / 1024, 6),
        "resident_fraction_of_full_params": round(
            resident_params / g.total_params, 9
        ),
    }


def panel() -> dict:
    g = MoEGeometry()
    g.validate()

    cache_slots = [8, 16, 32, 64]
    routing_alphas = [0.0, 0.75, 1.25]
    bandwidths = [1000.0, 2500.0, 5000.0]

    rows = [
        evaluate(cache, alpha, bw, geometry=g)
        for cache in cache_slots
        for alpha in routing_alphas
        for bw in bandwidths
    ]

    union_horizons = [1, 4, 16, 64, 256]
    union = [
        {
            "tokens": t,
            "expected_distinct_experts_per_layer_uniform": round(
                uniform_expected_distinct_experts(t, g), 9
            ),
        }
        for t in union_horizons
    ]

    return {
        "experiment": "FR-ELYZA-MOE-001",
        "status": "PASS",
        "claim_ceiling": "ANALYTIC_ROUTING_RESIDENCY_SHADOW_MODEL_ONLY",
        "geometry": {
            "layers": g.layers,
            "experts_per_layer": g.experts_per_layer,
            "active_experts_per_token": g.active_experts_per_token,
            "expert_params": g.expert_params,
            "all_expert_params": g.all_expert_params,
            "shared_params": g.shared_params,
            "published_total_params": g.total_params,
            "published_active_params": g.active_params,
            "derived_active_params": g.derived_active_params,
            "full_bf16_gib": round(params_to_mib(g.total_params, 2) / 1024, 6),
            "active_bf16_gib": round(params_to_mib(g.active_params, 2) / 1024, 6),
        },
        "uniform_expert_union": union,
        "rows": rows,
    }


def main() -> None:
    print(json.dumps(panel(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
