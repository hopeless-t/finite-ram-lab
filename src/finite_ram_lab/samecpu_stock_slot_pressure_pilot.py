from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .age_decoupling_stage_a import (
    Q64_EVENT,
    REFILL_EVENT,
    OWNER_UNCHARGE_EVENT,
    _prepare_refill_preverify,
)
from .memcg005gc_controlled_spawn import _stop, environment_receipt
from .obs005_cross_cgroup_lru import (
    CMD_TOUCH,
    _command as _helper_command,
    _start_role,
    _stop_role,
)
from .owner_refill_hist_pilot import (
    _cleanup_refill,
    _configure_hist,
    _hist_hits,
    _hist_text,
)
from .startup_stock_seed_phase import _delta_counts, _profile_counts
from .transaction_epoch_archive import EpochArchive
from .transaction_trace_observer import observer_receipt_for_window
from .transactional_reprime import State
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)
from .tx_perturbation_matrix import (
    TARGET_COMM,
    _close_owner_probe,
    _consume_segment,
    _fresh_epoch,
)


PRESSURE_TOUCH = 7300


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _profile_snapshot(trace_path: Path) -> dict[str, Any]:
    return {
        name: _profile_counts(trace_path, name)
        for name in (
            Q64_EVENT,
            REFILL_EVENT,
            OWNER_UNCHARGE_EVENT,
        )
    }


def _profile_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    return {
        name: _delta_counts(before.get(name), after.get(name))
        for name in before
    }


def _coverage_ok(delta: dict[str, Any]) -> bool:
    return all(
        row is not None and int(row.get("missed", -1)) == 0
        for row in delta.values()
    )


def _hist_dropped(text: str) -> int | None:
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw.startswith("Dropped:"):
            continue
        try:
            return int(raw.split(":", 1)[1].strip())
        except ValueError:
            return None
    return None


def _pressure_window(
    trace_path: Path,
    *,
    trial_id: str,
    epoch: int,
) -> dict[str, Any]:
    return observed_window(
        trace_text=trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        ),
        trial_id=trial_id,
        epoch=epoch,
        phase="OBSERVE",
        touch_number=PRESSURE_TOUCH,
    )


def _pressure_receipt(
    trace_path: Path,
    *,
    trial_id: str,
    epoch: int,
    owner_counter: str,
    owner_memcg: str,
    stock_cpu: int,
) -> dict[str, Any]:
    return observer_receipt_for_window(
        _pressure_window(
            trace_path,
            trial_id=trial_id,
            epoch=epoch,
        ),
        owner_counter=owner_counter,
        owner_memcg=owner_memcg,
        stock_cpu=stock_cpu,
        phase="OBSERVE",
        owner_probe_filtered=True,
    )


def _helper_q64_count(
    trace_path: Path,
    *,
    trial_id: str,
    epoch: int,
    stock_cpu: int,
) -> int:
    window = _pressure_window(
        trace_path,
        trial_id=trial_id,
        epoch=epoch,
    )
    return sum(
        1
        for row in window.get("pc_try64", [])
        if (
            row.get("comm") == "frltrig"
            and int(row.get("cpu", -1)) == int(stock_cpu)
        )
    )


def _drain_pages(receipt: dict[str, Any]) -> list[int]:
    pages: list[int] = []
    for item in receipt.get("target_drain_events", []):
        row = item.get("paired_page_counter_uncharge", {})
        try:
            pages.append(int(row["nr_pages"]))
        except (KeyError, TypeError, ValueError):
            continue
    return pages


def _prime_helper_until_q64(
    *,
    helper: dict[str, Any],
    trace_path: Path,
    trial_id: str,
    epoch: int,
    stock_cpu: int,
    max_touches: int = 65,
) -> dict[str, Any]:
    before = _helper_q64_count(
        trace_path,
        trial_id=trial_id,
        epoch=epoch,
        stock_cpu=stock_cpu,
    )

    # Startup itself may already have emitted a direct Q64 after exec.
    if before > 0:
        return {
            "realized": True,
            "touches": 0,
            "q64_count_before": before,
            "q64_count_after": before,
            "startup_or_prior_q64": True,
        }

    rows: list[dict[str, Any]] = []
    for touch in range(1, int(max_touches) + 1):
        row = _helper_command(helper, CMD_TOUCH)
        rows.append({"touch": touch, **row})
        after = _helper_q64_count(
            trace_path,
            trial_id=trial_id,
            epoch=epoch,
            stock_cpu=stock_cpu,
        )
        if after > before:
            return {
                "realized": True,
                "touches": touch,
                "q64_count_before": before,
                "q64_count_after": after,
                "startup_or_prior_q64": False,
                "rows": rows,
            }

    after = _helper_q64_count(
        trace_path,
        trial_id=trial_id,
        epoch=epoch,
        stock_cpu=stock_cpu,
    )
    return {
        "realized": after > before,
        "touches": int(max_touches),
        "q64_count_before": before,
        "q64_count_after": after,
        "startup_or_prior_q64": False,
        "rows": rows,
    }


def classify_trial(
    *,
    precondition_ok: bool,
    coverage_ok: bool,
    hist_dropped: int | None,
    pressure_trace_complete: bool,
    pressure_unknown_count: int,
    pressure_owner_refill_delta: int,
    target_drain_count: int,
    drain_pages: list[int],
    helpers_started: int,
    all_started_helpers_realized: bool,
    diagnostic_q64_count: int,
) -> str:
    if not precondition_ok:
        return "PRECONDITION_HOLD"
    if not coverage_ok or hist_dropped not in {0}:
        return "INSTRUMENTATION_HOLD"
    if not pressure_trace_complete:
        return "TRACE_HOLD"
    if pressure_unknown_count > 0:
        return "UNKNOWN_COMPLETE_EMISSION"
    if pressure_owner_refill_delta > 0:
        return "PRESSURE_CONFOUNDED_BY_OWNER_REFILL"
    if target_drain_count <= 0:
        if helpers_started >= 13 and all_started_helpers_realized:
            return "SLOT_EVICTION_BOUND_VIOLATION_CANDIDATE"
        return "HELPER_INSERTION_NOT_REALIZED"
    if drain_pages != [31]:
        return "TARGET_DRAIN_SIZE_MISMATCH"
    if diagnostic_q64_count == 1:
        return "EVICTION_FINGERPRINT_MATCH"
    return "EVICTION_BOUNDARY_MISMATCH"


def run_trial(
    *,
    spec: dict[str, Any],
    target_worker: Path,
    helper_worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    identity = 0
    trial_id = f"{block}:{identity}"
    archive = EpochArchive.start(max_reprimes=0)
    unit = None
    helpers: list[dict[str, Any]] = []
    helper_rows: list[dict[str, Any]] = []
    diagnostic: dict[str, Any] | None = None

    _prepare_refill_preverify(trace_path)

    try:
        (
            unit,
            geometry,
            sequence,
            page_size,
            cursor,
            measured_count,
            epoch_row,
        ) = _fresh_epoch(
            archive=archive,
            worker=target_worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            block=block,
            identity=identity,
            arm="SAMECPU_SLOT_PRESSURE",
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=256,
            calibration_max=65,
        )

        normalized = (
            archive.tx.state is State.VERIFIED
            and archive.owner_counter is not None
            and archive.owner_memcg is not None
        )
        if not normalized:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "block": block,
                "classification": "PRECONDITION_HOLD",
                "reason": archive.tx.invalidation_reason,
                "archive": archive.as_dict(),
            }

        cursor, measured_count, consume = _consume_segment(
            archive=archive,
            unit=unit,
            sequence=sequence,
            cursor=cursor,
            start_touch=1,
            count=int(spec["design"]["consume_before_pressure"]),
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            stock_cpu=stock_cpu,
            page_size=page_size,
            measured_count=measured_count,
        )
        epoch_row["consume_before_pressure"] = consume

        residual_before = archive.tx.expected_residual
        precondition_ok = (
            archive.tx.state in {State.VERIFIED, State.EXECUTING}
            and residual_before
            == int(spec["design"]["expected_residual_before_pressure"])
        )

        if not precondition_ok:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "block": block,
                "classification": "PRECONDITION_HOLD",
                "reason": archive.tx.invalidation_reason
                or f"expected_residual={residual_before}",
                "expected_residual": residual_before,
                "archive": archive.as_dict(),
            }

        _configure_hist(trace_path, archive.owner_memcg)
        hist_before_text = _hist_text(trace_path)
        hist_before = _hist_hits(hist_before_text) or 0
        profile_before = _profile_snapshot(trace_path)

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=PRESSURE_TOUCH,
            edge="PRE",
        )

        drain_detected = False
        max_helpers = int(spec["design"]["max_distinct_helpers"])
        for helper_index in range(1, max_helpers + 1):
            helper_root = (
                out_root
                / f"trial-{block}-{identity}"
                / f"helper-{helper_index}"
            )
            helper_root.mkdir(parents=True, exist_ok=True)
            helper = _start_role(
                worker=helper_worker,
                root=helper_root,
                name=(
                    f"fr-slot-{os.getenv('GITHUB_RUN_ID', 'local')}-"
                    f"{block}-{helper_index}"
                ),
                role="trigger",
                cpu=stock_cpu,
                max_pages=128,
                worker_uid=worker_uid,
                restrict_cpuset=True,
            )
            helpers.append(helper)

            receipt_after_start = _pressure_receipt(
                trace_path,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                owner_counter=archive.owner_counter,
                owner_memcg=archive.owner_memcg,
                stock_cpu=stock_cpu,
            )
            if int(receipt_after_start.get("drain_stock_count", 0)) > 0:
                helper_rows.append(
                    {
                        "helper_index": helper_index,
                        "drain_detected_during_startup": True,
                        "prime": None,
                    }
                )
                drain_detected = True
                break

            prime = _prime_helper_until_q64(
                helper=helper,
                trace_path=trace_path,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                stock_cpu=stock_cpu,
                max_touches=65,
            )
            receipt = _pressure_receipt(
                trace_path,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                owner_counter=archive.owner_counter,
                owner_memcg=archive.owner_memcg,
                stock_cpu=stock_cpu,
            )
            helper_rows.append(
                {
                    "helper_index": helper_index,
                    "drain_detected_during_startup": False,
                    "prime": prime,
                    "target_drain_count_cumulative": int(
                        receipt.get("drain_stock_count", 0)
                    ),
                }
            )
            if int(receipt.get("drain_stock_count", 0)) > 0:
                drain_detected = True
                break

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=PRESSURE_TOUCH,
            edge="POST",
        )

        pressure_window = _pressure_window(
            trace_path,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
        )
        pressure_receipt = observer_receipt_for_window(
            pressure_window,
            owner_counter=archive.owner_counter,
            owner_memcg=archive.owner_memcg,
            stock_cpu=stock_cpu,
            phase="OBSERVE",
            owner_probe_filtered=True,
        )

        hist_pressure_text = _hist_text(trace_path)
        hist_pressure = _hist_hits(hist_pressure_text)
        pressure_owner_refill_delta = (
            0
            if hist_pressure is None
            else int(hist_pressure) - int(hist_before)
        )
        hist_dropped = _hist_dropped(hist_pressure_text)

        # Physical diagnostic: exactly one fresh target page after pressure.
        diagnostic_touch_number = 1
        measured_count += 1
        touch = touch_with_transaction_marker(
            unit=unit,
            stock_cpu=stock_cpu,
            page_size=page_size,
            page_index=sequence[cursor],
            phase="TARGET",
            touch_number=diagnostic_touch_number,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            trace_marker=trace_marker,
        )
        cursor += 1
        diag_window = observed_window(
            trace_text=trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="TARGET",
            touch_number=diagnostic_touch_number,
        )
        diag_receipt = observer_receipt_for_window(
            diag_window,
            owner_counter=archive.owner_counter,
            owner_memcg=archive.owner_memcg,
            stock_cpu=stock_cpu,
            phase="TARGET",
            target_comm=TARGET_COMM,
            owner_probe_filtered=True,
        )
        diagnostic_q64_count = int(
            diag_receipt.get("page_counter_try_charge_64_count", 0)
        )
        diagnostic = {
            "T": 33,
            "touch": touch,
            "receipt": diag_receipt,
            "q64_count": diagnostic_q64_count,
        }

        profile_after = _profile_snapshot(trace_path)
        profile_delta = _profile_delta(profile_before, profile_after)
        coverage_ok = _coverage_ok(profile_delta)

        pages = _drain_pages(pressure_receipt)
        all_started_helpers_realized = all(
            row.get("drain_detected_during_startup")
            or bool((row.get("prime") or {}).get("realized"))
            for row in helper_rows
        )

        classification = classify_trial(
            precondition_ok=precondition_ok,
            coverage_ok=coverage_ok,
            hist_dropped=hist_dropped,
            pressure_trace_complete=bool(
                pressure_receipt.get("trace_complete", False)
            ),
            pressure_unknown_count=int(
                pressure_receipt.get("unknown_emission_count", 0)
            ),
            pressure_owner_refill_delta=int(
                pressure_owner_refill_delta
            ),
            target_drain_count=int(
                pressure_receipt.get("drain_stock_count", 0)
            ),
            drain_pages=pages,
            helpers_started=len(helpers),
            all_started_helpers_realized=all_started_helpers_realized,
            diagnostic_q64_count=diagnostic_q64_count,
        )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "classification": classification,
            "normalized": normalized,
            "expected_residual_before_pressure": residual_before,
            "owner_counter": archive.owner_counter,
            "owner_memcg": archive.owner_memcg,
            "geometry": geometry,
            "helpers_started": len(helpers),
            "helper_rows": helper_rows,
            "all_started_helpers_realized": all_started_helpers_realized,
            "drain_detected": drain_detected,
            "pressure_receipt": pressure_receipt,
            "target_drain_pages": pages,
            "pressure_owner_refill_delta": int(
                pressure_owner_refill_delta
            ),
            "hist_before_hits": int(hist_before),
            "hist_pressure_hits": hist_pressure,
            "hist_dropped": hist_dropped,
            "profile_delta": profile_delta,
            "coverage_ok": coverage_ok,
            "diagnostic": diagnostic,
            "predicted_T": 33,
            "predicted_delta": -31,
            "observed_fingerprint_match": (
                classification == "EVICTION_FINGERPRINT_MATCH"
            ),
            "archive": archive.as_dict(),
        }
    finally:
        _cleanup_refill(trace_path)
        _close_owner_probe(trace_path)
        for helper in reversed(helpers):
            _stop_role(helper)
        if unit is not None:
            _stop(unit)


def run_block(
    *,
    spec: dict[str, Any],
    target_worker: Path,
    helper_worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    worker_uid: int,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("slot-pressure pilot requires >=3 CPUs")
    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "environment.json").write_text(
        json.dumps(
            environment_receipt(target_worker, cpus),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    row = run_trial(
        spec=spec,
        target_worker=target_worker,
        helper_worker=helper_worker,
        out_root=out_root,
        trace_marker=trace_marker,
        trace_path=trace_path,
        block=block,
        prep_cpu=prep_cpu,
        stock_cpu=stock_cpu,
        worker_uid=worker_uid,
    )
    (out_root / f"trial-{block}-0.json").write_text(
        json.dumps(row, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "classification": row["classification"],
        "helpers_started": row.get("helpers_started"),
        "target_drain_pages": row.get("target_drain_pages"),
        "diagnostic_q64_count": (
            None
            if row.get("diagnostic") is None
            else row["diagnostic"].get("q64_count")
        ),
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    classifications = Counter(
        row.get("classification", "MISSING")
        for row in trials
    )
    matches = [
        row
        for row in trials
        if row.get("classification")
        == "EVICTION_FINGERPRINT_MATCH"
    ]
    zero_miss_evictions = [
        row
        for row in trials
        if (
            bool(row.get("coverage_ok"))
            and int(
                row.get("pressure_receipt", {}).get(
                    "drain_stock_count",
                    0,
                )
            )
            > 0
        )
    ]
    helper_counts = [
        int(row["helpers_started"])
        for row in zero_miss_evictions
        if row.get("helpers_started") is not None
    ]

    pilot_pass = (
        len(trials) == int(spec["design"]["total_identities"])
        and len(zero_miss_evictions) >= 1
        and len(matches) >= 1
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "classifications": dict(classifications),
        "zero_miss_target_eviction_count": len(zero_miss_evictions),
        "fingerprint_match_count": len(matches),
        "fingerprint_match_trials": [
            row["trial_id"] for row in matches
        ],
        "helper_count_to_eviction": helper_counts,
        "pilot_pass": pilot_pass,
        "trials": trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--spec", required=True)
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--target-worker", required=True)
    run.add_argument("--helper-worker", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--trace-marker", required=True)
    run.add_argument("--trace-path", required=True)
    run.add_argument("--worker-uid", type=int, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--spec", required=True)
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        result = run_block(
            spec=spec,
            target_worker=Path(args.target_worker).resolve(),
            helper_worker=Path(args.helper_worker).resolve(),
            out_root=Path(args.out_root),
            trace_marker=Path(args.trace_marker),
            trace_path=Path(args.trace_path),
            block=args.block,
            worker_uid=args.worker_uid,
        )
        print(json.dumps(result, sort_keys=True))
        return

    result = aggregate(spec, Path(args.input_root))
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "pilot_pass": result["pilot_pass"],
                "trial_count": result["trial_count"],
                "classifications": result["classifications"],
                "zero_miss_target_eviction_count": result[
                    "zero_miss_target_eviction_count"
                ],
                "fingerprint_match_count": result[
                    "fingerprint_match_count"
                ],
                "fingerprint_match_trials": result[
                    "fingerprint_match_trials"
                ],
                "helper_count_to_eviction": result[
                    "helper_count_to_eviction"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
