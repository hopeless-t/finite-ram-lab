from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class FloorCell:
    total_post_scan_mib: float

    def __post_init__(self) -> None:
        if not isinstance(self.total_post_scan_mib, (int, float)):
            raise ValueError("total_post_scan_mib_invalid")
        if self.total_post_scan_mib < 0:
            raise ValueError("total_post_scan_mib_negative")


def legacy_post_observer_floor(cells: Iterable[FloorCell]) -> float:
    values = [float(cell.total_post_scan_mib) for cell in cells]
    if not values:
        raise ValueError("no_floor_cells")
    return float(median(values))


def transient_excess_over_legacy_floor(
    *,
    transient_base_mib: float,
    legacy_floor_mib: float,
) -> float:
    if transient_base_mib < legacy_floor_mib:
        raise ValueError("transient_base_below_floor")
    return float(transient_base_mib - legacy_floor_mib)


def partially_identified_frontier(
    *,
    transient_base_mib: float,
    legacy_post_observer_floor_mib: float,
) -> dict[str, object]:
    excess = transient_excess_over_legacy_floor(
        transient_base_mib=transient_base_mib,
        legacy_floor_mib=legacy_post_observer_floor_mib,
    )
    return {
        "identity": "B_peak = B_clean + O_observer + E_transient",
        "observed_legacy_identity": (
            "B_legacy_post = B_clean + O_observer"
        ),
        "identified": {
            "B_peak_mib": transient_base_mib,
            "B_legacy_post_mib": legacy_post_observer_floor_mib,
            "E_transient_relative_to_legacy_mib": excess,
        },
        "not_identified_from_same_historical_trials": (
            "B_clean_mib",
            "O_observer_mib",
            "E_transient_relative_to_clean_mib",
        ),
    }
