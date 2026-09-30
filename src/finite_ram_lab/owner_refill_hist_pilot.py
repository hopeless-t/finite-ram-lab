from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .age_decoupling_stage_a import (
    Q64_EVENT,
    REFILL_EVENT,
    _close_refill_probe,
    _prepare_refill_preverify,
)
from .memcg005gc_controlled_spawn import _stop, environment_receipt
from .startup_stock_seed_phase import _delta_counts, _profile_counts
from .transaction_epoch_archive import EpochArchive
from .transactional_spawn_native import observed_window, write_marker
from .tx_perturbation_matrix import (
    _close_owner_probe,
    _fresh_epoch,
)


OWNER_UNCHARGE_EVENT = "frl_pc_uncharge_owner"
OBSERVE_TOUCH = 9900
HITS_RE = re.compile(r"\bHits:\s*(?P<hits>\d+)\b")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _refill_dir(trace_path: Path) -> Path:
    return trace_path.parent / "events" / "kprobes" / REFILL_EVENT


def _remove_hist_trigger(trace_path: Path) -> None:
    trigger = _refill_dir(trace_path) / "trigger"
    try:
        trigger.write_text("!hist:keys=nr_pages\n", encoding="utf-8")
    except OSError:
        pass


def _configure_log(trace_path: Path, owner_memcg: str) -> None:
    probe = _refill_dir(trace_path)
    _remove_hist_trigger(trace_path)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    (probe / "filter").write_text(
        f"memcg == {owner_memcg}\n",
        encoding="utf-8",
    )
    (probe / "enable").write_text("1\n", encoding="utf-8")


def _hist_trigger(owner_memcg: str) -> str:
    return f"hist:keys=nr_pages if memcg == {owner_memcg}"


def _configure_hist(trace_path: Path, owner_memcg: str) -> None:
    probe = _refill_dir(trace_path)
    _remove_hist_trigger(trace_path)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    # The event filter controls ordinary event logging, but histogram
    # triggers have their own filter clause. Keep both explicit.
    (probe / "filter").write_text(
        f"memcg == {owner_memcg}\n",
        encoding="utf-8",
    )
    (probe / "trigger").write_text(
        _hist_trigger(owner_memcg) + "\n",
        encoding="utf-8",
    )


def _hist_text(trace_path: Path) -> str:
    path = _refill_dir(trace_path) / "hist"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _hist_hits(text: str) -> int | None:
    match = HITS_RE.search(text)
    return None if match is None else int(match.group("hits"))


def _cleanup_refill(trace_path: Path) -> None:
    probe = _refill_dir(trace_path)
    try:
        (probe / "enable").write_text("0\n", encoding="utf-8")
    except OSError:
        pass
    _remove_hist_trigger(trace_path)
    try:
        (probe / "filter").write_text(
            "memcg == 0\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def run_identity(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    mode = str(spec["design"]["frozen_order"][identity])
    trial_id = f"0:{identity}"
    archive = EpochArchive.start(max_reprimes=0)
    unit = None

    try:
        _prepare_refill_preverify(trace_path)
        (
            unit,
            geometry,
            _sequence,
            _page_size,
            _cursor,
            _measured_count,
            _epoch_row,
        ) = _fresh_epoch(
            archive=archive,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            block=0,
            identity=identity,
            arm=f"REFILL_{mode}",
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=192,
            calibration_max=65,
        )

        if archive.owner_memcg is None or archive.owner_counter is None:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "identity": identity,
                "mode": mode,
                "valid": False,
                "reason": "OWNER_NOT_RESOLVED",
            }

        if mode == "LOG":
            _configure_log(trace_path, archive.owner_memcg)
        elif mode == "HIST":
            _configure_hist(trace_path, archive.owner_memcg)
        else:
            raise ValueError(f"unknown mode {mode}")

        before = {
            "refill": _profile_counts(trace_path, REFILL_EVENT),
            "q64": _profile_counts(trace_path, Q64_EVENT),
            "uncharge": _profile_counts(
                trace_path,
                OWNER_UNCHARGE_EVENT,
            ),
        }

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=OBSERVE_TOUCH,
            edge="PRE",
        )
        time.sleep(float(spec["design"]["observation_seconds"]))
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=OBSERVE_TOUCH,
            edge="POST",
        )
        time.sleep(0.002)

        after = {
            "refill": _profile_counts(trace_path, REFILL_EVENT),
            "q64": _profile_counts(trace_path, Q64_EVENT),
            "uncharge": _profile_counts(
                trace_path,
                OWNER_UNCHARGE_EVENT,
            ),
        }
        delta = {
            key: _delta_counts(before[key], after[key])
            for key in before
        }

        trace_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        window = observed_window(
            trace_text=trace_text,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=OBSERVE_TOUCH,
        )
        log_count = len(window.get("refill_stock", []))
        hist_text = _hist_text(trace_path) if mode == "HIST" else ""
        hist_hits = _hist_hits(hist_text) if mode == "HIST" else None

        refill_delta = delta["refill"]
        refill_missed = (
            None
            if refill_delta is None
            else int(refill_delta["missed"])
        )
        observed_owner_refills = (
            log_count if mode == "LOG" else hist_hits
        )

        valid = (
            bool(window.get("pre_count") == 1)
            and bool(window.get("post_count") == 1)
            and refill_delta is not None
            and observed_owner_refills is not None
        )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "identity": identity,
            "mode": mode,
            "owner_memcg": archive.owner_memcg,
            "owner_counter": archive.owner_counter,
            "geometry": geometry,
            "observation_seconds": float(
                spec["design"]["observation_seconds"]
            ),
            "profile_delta": delta,
            "refill_missed": refill_missed,
            "owner_refill_observed_count": observed_owner_refills,
            "log_refill_count": log_count,
            "hist_hits": hist_hits,
            "histogram_text": hist_text,
            "trace_complete": (
                int(window.get("pre_count", 0)) == 1
                and int(window.get("post_count", 0)) == 1
                and int(window.get("marker_error_count", 0)) == 0
            ),
            "state_after": archive.tx.state.value,
            "valid": valid,
        }
    finally:
        _cleanup_refill(trace_path)
        _close_owner_probe(trace_path)
        if unit is not None:
            _stop(unit)


def run_panel(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    worker_uid: int,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("refill hist pilot requires >=3 CPUs")

    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})
    out_root.mkdir(parents=True, exist_ok=True)

    (out_root / "environment.json").write_text(
        json.dumps(
            environment_receipt(worker, cpus),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    for identity in range(int(spec["design"]["identities"])):
        row = run_identity(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            identity=identity,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
        )
        (out_root / f"trial-0-{identity}.json").write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rows.append(row)

    by_mode: dict[str, dict[str, Any]] = {}
    for mode in ("LOG", "HIST"):
        subset = [row for row in rows if row["mode"] == mode]
        by_mode[mode] = {
            "n": len(subset),
            "valid": sum(bool(row.get("valid")) for row in subset),
            "refill_missed_total": sum(
                int(row.get("refill_missed") or 0)
                for row in subset
            ),
            "refill_miss_trials": [
                row["trial_id"]
                for row in subset
                if int(row.get("refill_missed") or 0) > 0
            ],
            "owner_refill_counts": [
                row.get("owner_refill_observed_count")
                for row in subset
            ],
        }

    hist_activity = any(
        int(row.get("hist_hits") or 0) > 0
        for row in rows
        if row["mode"] == "HIST"
    )
    pilot_pass = (
        by_mode["HIST"]["valid"] == 4
        and hist_activity
        and int(by_mode["HIST"]["refill_missed_total"])
        <= int(by_mode["LOG"]["refill_missed_total"])
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(rows),
        "by_mode": by_mode,
        "hist_activity_observed": hist_activity,
        "pilot_pass": pilot_pass,
        "trials": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--worker", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--trace-marker", required=True)
    parser.add_argument("--trace-path", required=True)
    parser.add_argument("--worker-uid", type=int, required=True)
    args = parser.parse_args()

    result = run_panel(
        spec=load_spec(args.spec),
        worker=Path(args.worker).resolve(),
        out_root=Path(args.out_root),
        trace_marker=Path(args.trace_marker),
        trace_path=Path(args.trace_path),
        worker_uid=args.worker_uid,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
