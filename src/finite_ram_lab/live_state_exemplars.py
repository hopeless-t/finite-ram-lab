from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

AXES = ("P", "A", "Q", "C", "T", "epsilon")
MOVES = frozenset({"COMPRESS", "REDUCE", "REMATERIALIZE", "MOVE", "SHARE", "REORDER"})


@dataclass(frozen=True)
class CostPoint:
    peak_live_bytes: float
    byte_seconds: float
    traffic_bytes: float
    compute_units: float
    latency_units: float
    error_units: float

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")

    def vector(self) -> tuple[float, ...]:
        return (
            float(self.peak_live_bytes),
            float(self.byte_seconds),
            float(self.traffic_bytes),
            float(self.compute_units),
            float(self.latency_units),
            float(self.error_units),
        )


@dataclass(frozen=True)
class Exemplar:
    name: str
    moves: tuple[str, ...]
    logical_frontier_effect: str
    physical_frontier_effect: str
    evidence_level: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        if any(move not in MOVES for move in self.moves):
            raise ValueError("move_invalid")
        if not self.evidence_level:
            raise ValueError("evidence_level_empty")


def ozaki_i_symbolic(
    *,
    slices: int,
    a_slice_bytes: int,
    b_slice_bytes: int,
    accumulator_bytes: int,
    base_bytes: int = 0,
) -> dict[str, int]:
    if min(slices, a_slice_bytes, b_slice_bytes, accumulator_bytes, base_bytes) < 0:
        raise ValueError("negative_input")
    if slices < 1:
        raise ValueError("slices_invalid")
    peak = base_bytes + slices * (a_slice_bytes + b_slice_bytes) + accumulator_bytes
    gemms = slices * (slices + 1) // 2
    return {"peak_live_bytes": peak, "gemm_count": gemms}


def ozaki_ii_symbolic(
    *,
    moduli: int,
    a_residue_bytes: int,
    b_residue_bytes: int,
    accumulator_bytes: int,
    base_bytes: int = 0,
    resident_residue_pairs: int = 1,
) -> dict[str, int]:
    if min(
        moduli,
        a_residue_bytes,
        b_residue_bytes,
        accumulator_bytes,
        base_bytes,
        resident_residue_pairs,
    ) < 0:
        raise ValueError("negative_input")
    if moduli < 1 or resident_residue_pairs < 1:
        raise ValueError("count_invalid")
    peak = (
        base_bytes
        + resident_residue_pairs * (a_residue_bytes + b_residue_bytes)
        + accumulator_bytes
    )
    return {"peak_live_bytes": peak, "gemm_count": moduli}


def naive_attention_score_bytes(sequence_length: int, element_bytes: int) -> int:
    if sequence_length < 1 or element_bytes < 1:
        raise ValueError("attention_input_invalid")
    return sequence_length * sequence_length * element_bytes


def tiled_attention_score_bytes(block_rows: int, block_cols: int, element_bytes: int) -> int:
    if block_rows < 1 or block_cols < 1 or element_bytes < 1:
        raise ValueError("attention_input_invalid")
    return block_rows * block_cols * element_bytes


def deduplicated_bytes(
    *,
    object_bytes: int,
    replicas: int,
    metadata_bytes_per_replica: int = 0,
) -> dict[str, int]:
    if object_bytes < 0 or replicas < 1 or metadata_bytes_per_replica < 0:
        raise ValueError("dedup_input_invalid")
    before = object_bytes * replicas
    after = object_bytes + replicas * metadata_bytes_per_replica
    return {
        "before_bytes": before,
        "after_bytes": after,
        "saved_bytes": max(0, before - after),
    }


def phase_value_density(
    *,
    size_bytes: int,
    accesses: Mapping[str, float],
    fast_access_cost: float,
    slow_access_cost: float,
) -> dict[str, float]:
    if size_bytes <= 0:
        raise ValueError("size_bytes_invalid")
    if min(fast_access_cost, slow_access_cost) < 0:
        raise ValueError("access_cost_invalid")
    saved_per_access = max(0.0, slow_access_cost - fast_access_cost)
    out: dict[str, float] = {}
    for phase, access_count in accesses.items():
        if (
            not isinstance(access_count, (int, float))
            or not isfinite(access_count)
            or access_count < 0
        ):
            raise ValueError("phase_access_invalid")
        out[phase] = float(access_count) * saved_per_access / size_bytes
    return out


EXEMPLARS = (
    Exemplar(
        "Ozaki Scheme I",
        ("REORDER",),
        "materialized precision slices keep a wider logical frontier",
        "placement can move slices but does not remove logical slice liveness",
        "symbolic/source-mapped",
    ),
    Exemplar(
        "Ozaki Scheme II",
        ("REDUCE", "REORDER"),
        "streamed residues can be folded into reconstruction state and released",
        "one/few residue pairs need be resident at once in the streaming design",
        "symbolic/source-mapped",
    ),
    Exemplar(
        "FlashAttention",
        ("REDUCE", "REORDER"),
        "full score matrix need not be materialized",
        "tiles plus running exact attention state replace N^2 score storage",
        "symbolic/source-mapped",
    ),
    Exemplar(
        "PagedAttention",
        ("SHARE", "MOVE"),
        "logical KV information is retained",
        "paging/sharing reduce fragmentation and duplicate physical residency",
        "mechanism-mapped",
    ),
    Exemplar(
        "Checkmate/DTR",
        ("REMATERIALIZE",),
        "selected intermediate state is removed from the live frontier",
        "regeneration provenance substitutes for continuous residency",
        "mechanism-mapped",
    ),
    Exemplar(
        "FlexGen",
        ("MOVE", "COMPRESS"),
        "logical tensor graph is mostly unchanged",
        "GPU/CPU/disk placement and compression fit the physical frontier",
        "mechanism-mapped",
    ),
    Exemplar(
        "Strata",
        ("COMPRESS", "MOVE", "SHARE", "REORDER"),
        "model semantics retained while active state changes by phase",
        "expert/KV placement, sharing, borrowing, and unload alter residency",
        "mechanism-mapped",
    ),
)
