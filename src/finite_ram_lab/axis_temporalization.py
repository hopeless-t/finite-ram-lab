from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import ceil


def ceil_div(x: int, y: int) -> int:
    if type(x) is not int or type(y) is not int or x < 1 or y < 1:
        raise ValueError("axis_extent_invalid")
    return (x + y - 1) // y


@dataclass(frozen=True)
class AxisModel:
    m: int
    n: int
    k: int
    p: int
    memory_limit_bytes: int
    a_low_bytes: int = 1
    b_low_bytes: int = 1
    reduced_product_bytes: int = 1
    active_product_bytes: int = 4
    carried_summary_bytes: int = 4
    fixed_bytes: int = 0
    precision_streaming_proven: bool = False

    def __post_init__(self) -> None:
        for name in ("m", "n", "k", "p", "memory_limit_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name}_invalid")
        for name in (
            "a_low_bytes",
            "b_low_bytes",
            "reduced_product_bytes",
            "active_product_bytes",
            "carried_summary_bytes",
            "fixed_bytes",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name}_invalid")


@dataclass(frozen=True)
class AxisPlan:
    bm: int
    bn: int
    bk: int
    bp: int
    workspace_bytes: int
    invocations: int
    precision_temporalized: bool


def normalized_workspace(model: AxisModel, bm: int, bn: int, bk: int, bp: int) -> int:
    """Normalized live-state model for axis-temporalization experiments.

    It is intentionally not a GEMMul8 workspace formula.  B429 provides the
    source-backed GEMMul8 formula.  This model isolates the geometry of choosing
    which axes are resident simultaneously.
    """
    for block, extent, name in (
        (bm, model.m, "bm"),
        (bn, model.n, "bn"),
        (bk, model.k, "bk"),
        (bp, model.p, "bp"),
    ):
        if type(block) is not int or block < 1 or block > extent:
            raise ValueError(f"{name}_invalid")

    if bp < model.p and not model.precision_streaming_proven:
        raise ValueError("precision_temporalization_unproven")

    a_state = bm * bk * bp * model.a_low_bytes
    b_state = bn * bk * bp * model.b_low_bytes
    active_product = bm * bn * model.active_product_bytes

    if bp == model.p:
        reduced_state = bm * bn * model.p * model.reduced_product_bytes
        carried_summary = 0
    else:
        reduced_state = bm * bn * bp * model.reduced_product_bytes
        carried_summary = bm * bn * model.carried_summary_bytes

    return (
        model.fixed_bytes
        + a_state
        + b_state
        + active_product
        + reduced_state
        + carried_summary
    )


def invocation_count(model: AxisModel, bm: int, bn: int, bk: int, bp: int) -> int:
    return (
        ceil_div(model.m, bm)
        * ceil_div(model.n, bn)
        * ceil_div(model.k, bk)
        * ceil_div(model.p, bp)
    )


def candidate_blocks(extent: int) -> tuple[int, ...]:
    """Compact exact-search grid based on block counts and powers of two."""
    if type(extent) is not int or extent < 1:
        raise ValueError("extent_invalid")
    out = {1, extent}
    x = 1
    while x < extent:
        out.add(x)
        x *= 2
    for count in range(2, min(extent, 16) + 1):
        out.add(ceil(extent / count))
    return tuple(sorted(x for x in out if 1 <= x <= extent))


def enumerate_feasible_plans(model: AxisModel) -> tuple[AxisPlan, ...]:
    m_blocks = candidate_blocks(model.m)
    n_blocks = candidate_blocks(model.n)
    k_blocks = candidate_blocks(model.k)
    p_blocks = candidate_blocks(model.p) if model.precision_streaming_proven else (model.p,)

    plans: list[AxisPlan] = []
    for bm, bn, bk, bp in product(m_blocks, n_blocks, k_blocks, p_blocks):
        workspace = normalized_workspace(model, bm, bn, bk, bp)
        if workspace > model.memory_limit_bytes:
            continue
        plans.append(
            AxisPlan(
                bm=bm,
                bn=bn,
                bk=bk,
                bp=bp,
                workspace_bytes=workspace,
                invocations=invocation_count(model, bm, bn, bk, bp),
                precision_temporalized=bp < model.p,
            )
        )
    return tuple(plans)


def best_plan(model: AxisModel) -> AxisPlan | None:
    plans = enumerate_feasible_plans(model)
    if not plans:
        return None

    # Primary objective: minimum normalized invocation count.
    # Secondary: largest occupied workspace (use available memory rather than
    # over-fragmenting work), then larger spatial/precision tiles.
    return min(
        plans,
        key=lambda p: (
            p.invocations,
            -p.workspace_bytes,
            -(p.bm * p.bn * p.bk * p.bp),
            -p.bp,
            -p.bk,
            -p.bm,
            -p.bn,
        ),
    )


def classify_memory_move(
    *,
    peak_delta: float,
    traffic_delta: float,
    compute_delta: float,
    latency_delta: float,
    error_delta: float,
) -> str:
    """Separate Pareto improvements from memory-for-cost exchanges."""
    deltas = (peak_delta, traffic_delta, compute_delta, latency_delta, error_delta)
    if all(d <= 0 for d in deltas) and any(d < 0 for d in deltas):
        return "PARETO_IMPROVEMENT"
    if peak_delta < 0 and any(d > 0 for d in deltas[1:]):
        return "MEMORY_EXCHANGE"
    if peak_delta == 0 and all(d == 0 for d in deltas[1:]):
        return "NO_CHANGE"
    return "MIXED_OR_NONMEMORY"
