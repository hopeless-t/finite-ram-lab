from __future__ import annotations

import json
from dataclasses import asdict, dataclass


MIB_PER_DECIMAL_GB = 1_000_000_000 / (1024 * 1024)


@dataclass(frozen=True)
class ModelGeometry:
    name: str
    packed_size_gb: float
    block_count: int = 64
    backbone_params_b: float = 24.35
    embedding_head_params_b: float = 2.54

    @property
    def language_params_b(self) -> float:
        return self.backbone_params_b + self.embedding_head_params_b

    @property
    def packed_size_mib(self) -> float:
        return self.packed_size_gb * MIB_PER_DECIMAL_GB

    @property
    def backbone_mib(self) -> float:
        return self.packed_size_mib * self.backbone_params_b / self.language_params_b

    @property
    def pinned_nonblock_mib(self) -> float:
        return self.packed_size_mib - self.backbone_mib

    @property
    def block_mib(self) -> float:
        return self.backbone_mib / self.block_count


@dataclass(frozen=True)
class OutOfCoreCase:
    resident_budget_mib: float
    io_bandwidth_mib_s: float
    window_blocks: int = 2
    double_buffer: bool = True
    runtime_and_kv_reserve_mib: float = 768.0
    prefill_tokens: int = 4096


def evaluate(model: ModelGeometry, case: OutOfCoreCase) -> dict[str, float | int | bool]:
    buffer_multiplier = 2 if case.double_buffer else 1
    streaming_window_mib = model.block_mib * case.window_blocks * buffer_multiplier
    fixed_mib = (
        model.pinned_nonblock_mib
        + case.runtime_and_kv_reserve_mib
        + streaming_window_mib
    )
    free_for_pinned_blocks_mib = max(0.0, case.resident_budget_mib - fixed_mib)
    pinned_blocks = min(
        model.block_count,
        int(free_for_pinned_blocks_mib // model.block_mib),
    )
    streamed_blocks = model.block_count - pinned_blocks
    decode_io_mib_per_token = streamed_blocks * model.block_mib

    decode_io_bound_tps = (
        case.io_bandwidth_mib_s / decode_io_mib_per_token
        if decode_io_mib_per_token > 0
        else float("inf")
    )
    prefill_io_mib_per_token = (
        decode_io_mib_per_token / case.prefill_tokens
        if case.prefill_tokens > 0
        else float("inf")
    )
    prefill_io_bound_tps = (
        case.io_bandwidth_mib_s / prefill_io_mib_per_token
        if prefill_io_mib_per_token > 0
        else float("inf")
    )

    return {
        "feasible_window": case.resident_budget_mib >= fixed_mib,
        "fixed_mib": round(fixed_mib, 3),
        "block_mib": round(model.block_mib, 3),
        "pinned_blocks": pinned_blocks,
        "streamed_blocks": streamed_blocks,
        "decode_io_mib_per_token": round(decode_io_mib_per_token, 3),
        "decode_io_bound_tps": round(decode_io_bound_tps, 6),
        "prefill_io_mib_per_token": round(prefill_io_mib_per_token, 6),
        "prefill_io_bound_tps": round(prefill_io_bound_tps, 3),
    }


def panel() -> dict:
    models = {
        "PTQ1_0": ModelGeometry("Bonsai-2-27B PTQ1_0", 5.95),
        "PQ2_0": ModelGeometry("Bonsai-2-27B PQ2_0", 7.21),
    }
    budgets = (1024, 2048, 4096, 6144)
    bandwidths = (1000, 2500, 5000)

    rows = []
    for model_name, model in models.items():
        for budget in budgets:
            for bandwidth in bandwidths:
                case = OutOfCoreCase(
                    resident_budget_mib=budget,
                    io_bandwidth_mib_s=bandwidth,
                )
                rows.append(
                    {
                        "model": model_name,
                        "resident_budget_mib": budget,
                        "io_bandwidth_mib_s": bandwidth,
                        **evaluate(model, case),
                    }
                )

    return {
        "schema": "finite-ram-lab.fr-bonsai-001/v0.1",
        "status": "PASS",
        "claim_ceiling": "ANALYTIC_OUT_OF_CORE_LLM_SHADOW_MODEL_ONLY",
        "assumptions": {
            "transformer_blocks": 64,
            "language_backbone_params_b": 24.35,
            "embedding_lm_head_params_b": 2.54,
            "runtime_and_kv_reserve_mib": 768,
            "window_blocks": 2,
            "double_buffer": True,
            "prefill_tokens": 4096,
        },
        "rows": rows,
    }


def main() -> None:
    print(json.dumps(panel(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
