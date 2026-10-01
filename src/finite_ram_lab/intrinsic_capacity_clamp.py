from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ClampCell:
    memory_high_mib: float
    release_interval_mib: float
    peak_mib: float
    memory_high_events: float

    def __post_init__(self) -> None:
        for name in (
            "memory_high_mib",
            "release_interval_mib",
            "peak_mib",
            "memory_high_events",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                raise ValueError(f"{name}_invalid")
        if self.memory_high_mib <= 0 or self.release_interval_mib <= 0:
            raise ValueError("capacity_or_release_invalid")
        if self.peak_mib < 0 or self.memory_high_events < 0:
            raise ValueError("measurement_invalid")


def robust_transient_base(cells: Iterable[ClampCell]) -> float:
    candidates = [
        float(cell.peak_mib - cell.release_interval_mib)
        for cell in cells
        if cell.memory_high_events == 0
    ]
    if not candidates:
        raise ValueError("no_pressure_free_cells")
    return float(median(candidates))


def predicted_peak_mib(
    *,
    memory_high_mib: float,
    release_interval_mib: float,
    transient_base_mib: float,
) -> float:
    return float(
        min(
            memory_high_mib,
            transient_base_mib + release_interval_mib,
        )
    )


def predicted_pressure(
    *,
    memory_high_mib: float,
    release_interval_mib: float,
    transient_base_mib: float,
) -> bool:
    return transient_base_mib + release_interval_mib > memory_high_mib


def classify_cells(
    cells: Sequence[ClampCell],
    *,
    transient_base_mib: float,
) -> list[dict[str, float | bool]]:
    rows = []
    for cell in cells:
        pred_peak = predicted_peak_mib(
            memory_high_mib=cell.memory_high_mib,
            release_interval_mib=cell.release_interval_mib,
            transient_base_mib=transient_base_mib,
        )
        rows.append(
            {
                "memory_high_mib": cell.memory_high_mib,
                "release_interval_mib": cell.release_interval_mib,
                "observed_peak_mib": cell.peak_mib,
                "predicted_peak_mib": pred_peak,
                "peak_residual_mib": cell.peak_mib - pred_peak,
                "observed_pressure": cell.memory_high_events > 0,
                "predicted_pressure": predicted_pressure(
                    memory_high_mib=cell.memory_high_mib,
                    release_interval_mib=cell.release_interval_mib,
                    transient_base_mib=transient_base_mib,
                ),
            }
        )
    return rows


def pressure_classification_accuracy(
    rows: Sequence[dict[str, float | bool]],
) -> float:
    if not rows:
        raise ValueError("rows_empty")
    return sum(
        bool(row["observed_pressure"]) == bool(row["predicted_pressure"])
        for row in rows
    ) / len(rows)
