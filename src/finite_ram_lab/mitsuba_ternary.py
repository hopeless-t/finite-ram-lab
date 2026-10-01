from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

PRISM_RUNTIME_COMMIT = "88c4bc60b9c9578f134385be9535e853f2db9b9f"
MITSUBA_REPO = "isichan-ai/Mitsuba-ComfyUI-27B-GGUF"
MITSUBA_PQ2_FILE = "Mitsuba-ComfyUI-27B-v1.18-PQ2_0.gguf"
MITSUBA_PTQ1_FILE = "Mitsuba-ComfyUI-27B-v1.18-PTQ1_0.gguf"
MITSUBA_MMPROJ_FILE = "mmproj-Q8_0.gguf"
MITSUBA_MMPROJ_SHA256 = (
    "6807ede61d570bb86ba34b756a0fa109edc33668604de867c6ea6d8f1d631903"
)


@dataclass(frozen=True)
class PackingGeometry:
    name: str
    group_size: int
    packed_bytes: int
    scale_bytes: int

    @property
    def block_bytes(self) -> int:
        return self.packed_bytes + self.scale_bytes

    @property
    def bits_per_weight(self) -> float:
        return self.block_bytes * 8.0 / self.group_size


PQ2_0 = PackingGeometry("PQ2_0", group_size=128, packed_bytes=32, scale_bytes=2)
PTQ1_0 = PackingGeometry("PTQ1_0", group_size=128, packed_bytes=26, scale_bytes=2)
PACKINGS = {p.name: p for p in (PQ2_0, PTQ1_0)}


@dataclass(frozen=True)
class RuntimeIdentity:
    model_repo: str
    model_filename: str
    model_sha256: str
    projector_filename: str
    projector_sha256: str
    packing: str
    runtime_repo: str
    runtime_commit: str
    runtime_binary_sha256: str
    reasoning: str
    cache_type_k: str
    cache_type_v: str
    context_size: int

    def validate(self) -> None:
        if self.packing not in PACKINGS:
            raise ValueError("packing_not_qualified")
        if self.reasoning != "off":
            raise ValueError("mitsuba_reasoning_must_be_off")
        if self.context_size <= 0:
            raise ValueError("context_size_invalid")
        if not HEX40.fullmatch(self.runtime_commit):
            raise ValueError("runtime_commit_invalid")
        for label, value in (
            ("model_sha256", self.model_sha256),
            ("projector_sha256", self.projector_sha256),
            ("runtime_binary_sha256", self.runtime_binary_sha256),
        ):
            if not SHA256.fullmatch(value):
                raise ValueError(label + "_invalid")

    def canonical_bytes(self) -> bytes:
        self.validate()
        return json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @property
    def identity_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


def sha256_file(path: str | Path, *, chunk_bytes: int = 1024 * 1024) -> str:
    target = Path(path)
    h = sha256()
    with target.open("rb") as stream:
        while chunk := stream.read(chunk_bytes):
            h.update(chunk)
    return h.hexdigest()


def artifact_record(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    info = target.stat()
    if not target.is_file():
        raise ValueError("artifact_not_regular_file")
    return {
        "path": str(target),
        "bytes": int(info.st_size),
        "sha256": sha256_file(target),
    }


def static_resident_budget(
    *,
    model_bytes: int,
    projector_bytes: int,
    runtime_bytes: int = 0,
    kv_bytes: int = 0,
    other_bytes: int = 0,
) -> dict[str, int]:
    values = {
        "model_bytes": model_bytes,
        "projector_bytes": projector_bytes,
        "runtime_bytes": runtime_bytes,
        "kv_bytes": kv_bytes,
        "other_bytes": other_bytes,
    }
    if any(type(v) is not int or v < 0 for v in values.values()):
        raise ValueError("budget_bytes_invalid")
    total = sum(values.values())
    return {**values, "total_bytes": total}


def compare_packings(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    by_packing = {str(row["packing"]): row for row in materialized}
    if set(by_packing) != {"PQ2_0", "PTQ1_0"}:
        raise ValueError("comparison_requires_both_packings")
    pq = by_packing["PQ2_0"]
    pt = by_packing["PTQ1_0"]
    for row in (pq, pt):
        if row.get("weights_semantics") != "SAME_TERNARY_WEIGHTS":
            raise ValueError("weights_semantics_not_frozen")
        if not isinstance(row.get("peak_rss_bytes"), int):
            raise ValueError("peak_rss_missing")
    return {
        "schema": "finite-ram-lab.mitsuba-packing-comparison/v0.1",
        "pq2_peak_rss_bytes": pq["peak_rss_bytes"],
        "ptq1_peak_rss_bytes": pt["peak_rss_bytes"],
        "ptq1_minus_pq2_peak_rss_bytes": (
            pt["peak_rss_bytes"] - pq["peak_rss_bytes"]
        ),
        "same_weights_control": True,
        "claim_ceiling": (
            "Packing/runtime comparison only; no model-quality superiority claim."
        ),
    }
