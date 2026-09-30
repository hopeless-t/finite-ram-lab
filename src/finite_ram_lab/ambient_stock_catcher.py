from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

BASELINE_NEXT_Q64_T = 64
EXPECTED_INITIAL_RESIDUAL = 31

CLASSIFICATIONS = frozenset({
    "PREVERIFY_HOLD",
    "OBSERVATION_HOLD",
    "INSTRUMENTATION_HOLD",
    "CANARY_CONTAMINATED",
    "AMBIENT_Q64_RESET",
    "STABLE_RESIDUAL",
    "DIRECT_SLOT_EVICTION_FINGERPRINT",
    "DIRECT_STOCK_CONSUMPTION_FINGERPRINT",
    "REFILL_MUTATION_PRESENT",
    "MULTI_PATH_TRANSITION",
    "UNATTRIBUTED_OWNER_UNCHARGE",
    "BOUNDARY_CENSORED",
    "UNKNOWN_COMPLETE",
})


@dataclass(frozen=True)
class AmbientObservation:
    normalized: bool
    initial_residual: int
    ambient_target_touch_count: int
    ambient_owner_q64_count: int
    trace_complete: bool
    worker_ok: bool
    cpu_stable: bool
    pte_stable: bool
    critical_probe_missed: Mapping[str, int | None]
    hist_dropped: int
    owner_refill_pages: int
    owner_consume_pages: int
    target_drain_pages: int
    owner_uncharge_pages: int
    boundary_observed: bool
    final_boundary_T: int | None


def _nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name}_invalid")
    return value


def _validate(obs: AmbientObservation) -> None:
    for name in (
        "initial_residual",
        "ambient_target_touch_count",
        "ambient_owner_q64_count",
        "hist_dropped",
        "owner_refill_pages",
        "owner_consume_pages",
        "target_drain_pages",
        "owner_uncharge_pages",
    ):
        _nonnegative_int(getattr(obs, name), name)

    if not isinstance(obs.critical_probe_missed, Mapping):
        raise ValueError("critical_probe_missed_invalid")

    if obs.boundary_observed:
        if type(obs.final_boundary_T) is not int or obs.final_boundary_T < 1:
            raise ValueError("final_boundary_T_invalid")
    elif obs.final_boundary_T is not None:
        raise ValueError("boundary_censoring_inconsistent")


def _mechanisms(obs: AmbientObservation) -> tuple[str, ...]:
    out: list[str] = []
    if obs.target_drain_pages > 0:
        out.append("drain")
    if obs.owner_consume_pages > 0:
        out.append("consume")
    if obs.owner_refill_pages > 0:
        out.append("refill")
    return tuple(out)


def classify_ambient_stock(obs: AmbientObservation) -> dict[str, Any]:
    """Classify one bounded ambient canary session conservatively.

    Mechanism labels are promoted only when an isolated observed mechanism
    predicts the measured Q64 boundary exactly. Otherwise complete but
    unexplained cases remain UNKNOWN_COMPLETE.
    """
    _validate(obs)

    if not obs.normalized or obs.initial_residual != EXPECTED_INITIAL_RESIDUAL:
        return _result(obs, "PREVERIFY_HOLD", exact=False)

    if (
        not obs.trace_complete
        or not obs.worker_ok
        or not obs.cpu_stable
        or not obs.pte_stable
        or obs.hist_dropped != 0
    ):
        return _result(obs, "OBSERVATION_HOLD", exact=False)

    misses = tuple(obs.critical_probe_missed.values())
    if (
        not obs.critical_probe_missed
        or any(value is None for value in misses)
        or any(type(value) is not int or value != 0 for value in misses)
    ):
        return _result(obs, "INSTRUMENTATION_HOLD", exact=False)

    if obs.ambient_target_touch_count != 0:
        return _result(obs, "CANARY_CONTAMINATED", exact=False)

    if obs.ambient_owner_q64_count != 0:
        return _result(obs, "AMBIENT_Q64_RESET", exact=False)

    mechanisms = _mechanisms(obs)
    mechanism_count = len(mechanisms)

    if not obs.boundary_observed:
        if mechanism_count >= 2:
            classification = "MULTI_PATH_TRANSITION"
        elif obs.owner_refill_pages > 0:
            classification = "REFILL_MUTATION_PRESENT"
        else:
            classification = "BOUNDARY_CENSORED"
        return _result(obs, classification, exact=False)

    assert obs.final_boundary_T is not None
    t = obs.final_boundary_T

    if mechanism_count >= 2:
        return _result(obs, "MULTI_PATH_TRANSITION", exact=False)

    if obs.owner_refill_pages > 0:
        return _result(obs, "REFILL_MUTATION_PRESENT", exact=False)

    if mechanism_count == 0:
        if obs.owner_uncharge_pages > 0 and t != BASELINE_NEXT_Q64_T:
            classification = "UNATTRIBUTED_OWNER_UNCHARGE"
        elif obs.owner_uncharge_pages == 0 and t == BASELINE_NEXT_Q64_T:
            classification = "STABLE_RESIDUAL"
        else:
            classification = "UNKNOWN_COMPLETE"
        return _result(obs, classification, exact=False)

    if obs.target_drain_pages > 0:
        pages = obs.target_drain_pages
        predicted_t = BASELINE_NEXT_Q64_T - pages
        exact = (
            0 < pages <= EXPECTED_INITIAL_RESIDUAL
            and obs.critical_probe_missed.get("drain") == 0
            and obs.owner_uncharge_pages == pages
            and t == predicted_t
        )
        classification = (
            "DIRECT_SLOT_EVICTION_FINGERPRINT"
            if exact
            else "UNKNOWN_COMPLETE"
        )
        return _result(obs, classification, exact=exact, predicted_t=predicted_t)

    if obs.owner_consume_pages > 0:
        pages = obs.owner_consume_pages
        predicted_t = BASELINE_NEXT_Q64_T - pages
        exact = (
            0 < pages <= EXPECTED_INITIAL_RESIDUAL
            and obs.critical_probe_missed.get("consume") == 0
            and t == predicted_t
        )
        classification = (
            "DIRECT_STOCK_CONSUMPTION_FINGERPRINT"
            if exact
            else "UNKNOWN_COMPLETE"
        )
        return _result(obs, classification, exact=exact, predicted_t=predicted_t)

    return _result(obs, "UNKNOWN_COMPLETE", exact=False)


def _result(
    obs: AmbientObservation,
    classification: str,
    *,
    exact: bool,
    predicted_t: int | None = None,
) -> dict[str, Any]:
    if classification not in CLASSIFICATIONS:
        raise AssertionError("classification_not_registered")

    boundary_delta = (
        None
        if not obs.boundary_observed or obs.final_boundary_T is None
        else obs.final_boundary_T - BASELINE_NEXT_Q64_T
    )

    complete_nonpromoted = {
        "STABLE_RESIDUAL",
        "REFILL_MUTATION_PRESENT",
        "MULTI_PATH_TRANSITION",
        "UNATTRIBUTED_OWNER_UNCHARGE",
        "BOUNDARY_CENSORED",
        "UNKNOWN_COMPLETE",
    }

    return {
        "classification": classification,
        "boundary_delta": boundary_delta,
        "predicted_boundary_T": predicted_t,
        "exact_mechanistic_fingerprint": bool(exact),
        "mechanisms_present": list(_mechanisms(obs)),
        "claim_ceiling": (
            "DIRECT_MECHANISTIC_FINGERPRINT"
            if exact
            else (
                "COMPLETE_BUT_NONPROMOTED"
                if classification in complete_nonpromoted
                else "HOLD_ONLY"
            )
        ),
    }
