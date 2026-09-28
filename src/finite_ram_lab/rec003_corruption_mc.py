from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from .mc_quality import wilson_interval
from .recorder import EvidenceError, SCHEMA_VERSION, StreamContractValidator, validate_record

Record = dict[str, Any]
Mutator = Callable[[list[Record], random.Random], None]

MUTATION_NAMES = (
    "after_end",
    "second_end",
    "seq_gap",
    "duplicate_seq",
    "mixed_run_id",
    "bad_schema",
    "drop_start",
    "unknown_type",
    "missing_required",
    "nonfinite_sample",
    "empty_phase",
    "start_seq_nonzero",
)


def _base_record(run_id: str, seq: int, record_type: str, **extra: Any) -> Record:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "run_id": run_id,
        "seq": seq,
        "monotonic_ns": 1_000_000 + seq,
        "wall_time_utc": "2026-09-28T00:00:00.000000Z",
        **extra,
    }


def make_valid_run(rng: random.Random, *, complete: bool) -> list[Record]:
    run_id = f"mc-{rng.randrange(1 << 48):012x}"
    records: list[Record] = [
        _base_record(
            run_id,
            0,
            "run_start",
            experiment_id="REC-003-MC",
            spec_id="rec-003-corruption-v1",
            source_commit="synthetic",
            provenance={"note": "猫-Δ-✓", "seed_tag": rng.randrange(1 << 16)},
            config={"memory_high_mib": rng.choice([144, 160, 176])},
        )
    ]
    seq = 1
    for _ in range(rng.randint(3, 8)):
        kind = rng.choice(("sample", "event", "summary"))
        if kind == "sample":
            records.append(
                _base_record(
                    run_id,
                    seq,
                    "sample",
                    metric=rng.choice(("memory.current", "psi.some", "io.read")),
                    value=rng.uniform(0.0, 1_000_000.0),
                    unit=rng.choice(("bytes", "ratio", "count")),
                    phase=rng.choice(("scan", "retouch", "final")),
                )
            )
        elif kind == "event":
            records.append(
                _base_record(
                    run_id,
                    seq,
                    "event",
                    event=rng.choice(("pressure", "phase", "checkpoint")),
                    details={"text": "lambda/猫/line\\nvalue", "n": rng.randrange(1000)},
                )
            )
        else:
            records.append(
                _base_record(
                    run_id,
                    seq,
                    "summary",
                    metric="peak_memory",
                    value=rng.uniform(0.0, 1_000_000.0),
                    unit="bytes",
                    method="synthetic-max",
                    details={"window": rng.randrange(1, 65)},
                )
            )
        seq += 1
    if complete:
        records.append(_base_record(run_id, seq, "run_end", status="PASS", details={}))
    return records


def _sample(records: list[Record]) -> Record:
    for record in records:
        if record.get("record_type") == "sample":
            return record
    target = records[1]
    run_id = records[0]["run_id"]
    seq = target["seq"]
    target.clear()
    target.update(
        _base_record(
            run_id,
            seq,
            "sample",
            metric="memory.current",
            value=1.0,
            unit="bytes",
            phase="scan",
        )
    )
    return target


def mutate_after_end(records: list[Record], rng: random.Random) -> None:
    if records[-1]["record_type"] != "run_end":
        seq = records[-1]["seq"] + 1
        records.append(_base_record(records[0]["run_id"], seq, "run_end", status="PASS", details={}))
    seq = records[-1]["seq"] + 1
    records.append(_base_record(records[0]["run_id"], seq, "event", event="late", details={}))


def mutate_second_end(records: list[Record], rng: random.Random) -> None:
    if records[-1]["record_type"] != "run_end":
        seq = records[-1]["seq"] + 1
        records.append(_base_record(records[0]["run_id"], seq, "run_end", status="PASS", details={}))
    seq = records[-1]["seq"] + 1
    records.append(_base_record(records[0]["run_id"], seq, "run_end", status="PASS", details={}))


def mutate_seq_gap(records: list[Record], rng: random.Random) -> None:
    records[rng.randrange(1, len(records))]["seq"] += rng.randint(1, 3)


def mutate_duplicate_seq(records: list[Record], rng: random.Random) -> None:
    idx = rng.randrange(1, len(records))
    records[idx]["seq"] = records[idx - 1]["seq"]


def mutate_mixed_run_id(records: list[Record], rng: random.Random) -> None:
    records[rng.randrange(1, len(records))]["run_id"] = "foreign-run"


def mutate_bad_schema(records: list[Record], rng: random.Random) -> None:
    records[rng.randrange(len(records))]["schema_version"] = "rec-999-bad"


def mutate_drop_start(records: list[Record], rng: random.Random) -> None:
    records.pop(0)


def mutate_unknown_type(records: list[Record], rng: random.Random) -> None:
    records[rng.randrange(len(records))]["record_type"] = "telepathy"


def mutate_missing_required(records: list[Record], rng: random.Random) -> None:
    _sample(records).pop("metric", None)


def mutate_nonfinite_sample(records: list[Record], rng: random.Random) -> None:
    _sample(records)["value"] = float("inf")


def mutate_empty_phase(records: list[Record], rng: random.Random) -> None:
    _sample(records)["phase"] = ""


def mutate_start_seq_nonzero(records: list[Record], rng: random.Random) -> None:
    records[0]["seq"] = rng.randint(1, 4)


MUTATORS: dict[str, Mutator] = {
    "after_end": mutate_after_end,
    "second_end": mutate_second_end,
    "seq_gap": mutate_seq_gap,
    "duplicate_seq": mutate_duplicate_seq,
    "mixed_run_id": mutate_mixed_run_id,
    "bad_schema": mutate_bad_schema,
    "drop_start": mutate_drop_start,
    "unknown_type": mutate_unknown_type,
    "missing_required": mutate_missing_required,
    "nonfinite_sample": mutate_nonfinite_sample,
    "empty_phase": mutate_empty_phase,
    "start_seq_nonzero": mutate_start_seq_nonzero,
}


def strict_accepts(records: list[Record]) -> bool:
    stream = StreamContractValidator()
    try:
        for index, record in enumerate(records, start=1):
            stream.accept(record, context=f"world:{index}")
        return True
    except (EvidenceError, KeyError, TypeError, ValueError):
        return False


def legacy_relaxed_accepts(records: list[Record]) -> bool:
    seen_start: set[str] = set()
    try:
        for record in records:
            validate_record(record)
            run_id = record["run_id"]
            if record["record_type"] == "run_start":
                seen_start.add(run_id)
            elif run_id not in seen_start:
                return False
        return True
    except (EvidenceError, KeyError, TypeError, ValueError):
        return False


def run_campaign(worlds: int, seed: int, max_mutations: int = 4) -> dict[str, Any]:
    if worlds <= 0:
        raise ValueError("worlds must be positive")
    if max_mutations <= 0:
        raise ValueError("max_mutations must be positive")

    rng = random.Random(seed)
    false_accept = 0
    false_reject = 0
    legacy_false_accept = 0
    corrupt_worlds = 0
    valid_worlds = 0
    mutation_counts: Counter[str] = Counter()
    strict_accept_by_mutation: Counter[str] = Counter()
    checkpoints: list[dict[str, Any]] = []

    for world in range(1, worlds + 1):
        is_valid = rng.random() < 0.20
        records = make_valid_run(rng, complete=rng.random() < 0.80)

        if is_valid:
            valid_worlds += 1
            if not strict_accepts(records):
                false_reject += 1
        else:
            corrupt_worlds += 1
            k = rng.randint(1, min(max_mutations, len(MUTATION_NAMES)))
            chosen = rng.sample(MUTATION_NAMES, k)
            for name in chosen:
                MUTATORS[name](records, rng)
                mutation_counts[name] += 1

            strict = strict_accepts(records)
            relaxed = legacy_relaxed_accepts(records)
            if strict:
                false_accept += 1
                for name in chosen:
                    strict_accept_by_mutation[name] += 1
            if relaxed:
                legacy_false_accept += 1

        if world in {100, 1000, 5000, 10000, 25000, 50000, 100000, worlds}:
            checkpoints.append(
                {
                    "worlds": world,
                    "false_accept": false_accept,
                    "false_reject": false_reject,
                }
            )

    fa_ci = wilson_interval(false_accept, corrupt_worlds)
    fr_ci = wilson_interval(false_reject, valid_worlds)
    legacy_ci = wilson_interval(legacy_false_accept, corrupt_worlds)

    return {
        "campaign_id": "REC-003-MC-v1",
        "seed": seed,
        "worlds": worlds,
        "generator_scope": (
            "Synthetic corruption coverage only; rates are not estimates of real-world "
            "hardware, filesystem, or recorder failure probability."
        ),
        "valid_worlds": valid_worlds,
        "corrupt_worlds": corrupt_worlds,
        "strict_false_accept": false_accept,
        "strict_false_accept_rate": false_accept / corrupt_worlds if corrupt_worlds else 0.0,
        "strict_false_accept_ci95": list(fa_ci),
        "strict_false_reject": false_reject,
        "strict_false_reject_rate": false_reject / valid_worlds if valid_worlds else 0.0,
        "strict_false_reject_ci95": list(fr_ci),
        "legacy_negative_control_false_accept": legacy_false_accept,
        "legacy_negative_control_false_accept_rate": (
            legacy_false_accept / corrupt_worlds if corrupt_worlds else 0.0
        ),
        "legacy_negative_control_ci95": list(legacy_ci),
        "mutation_counts": dict(sorted(mutation_counts.items())),
        "strict_accept_by_mutation": dict(sorted(strict_accept_by_mutation.items())),
        "convergence": checkpoints,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=2026092807)
    parser.add_argument("--max-mutations", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run_campaign(args.worlds, args.seed, args.max_mutations)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

    if result["strict_false_accept"] or result["strict_false_reject"]:
        raise SystemExit(1)
    if result["legacy_negative_control_false_accept"] == 0:
        raise SystemExit("negative control did not admit any corrupt worlds")


if __name__ == "__main__":
    main()
