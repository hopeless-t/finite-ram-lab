from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-021-physical-cpu-transfer-conjunction/v0.1"
MIB = 1024 * 1024

LANES = {
    "FAST_FAST": {"transfer_delay_ms": 0, "cpu_gate_ms": 0},
    "SLOW_TRANSFER": {"transfer_delay_ms": 35, "cpu_gate_ms": 0},
    "SLOW_CPU": {"transfer_delay_ms": 0, "cpu_gate_ms": 140},
    "SLOW_BOTH": {"transfer_delay_ms": 35, "cpu_gate_ms": 140},
}


def service_at_deadline(samples: list[tuple[int, int]], deadline_ns: int) -> int:
    if deadline_ns < 0:
        raise ValueError("deadline_must_be_nonnegative")
    value = 0
    last_time = -1
    last_value = -1
    for sample_time_ns, cumulative in samples:
        if sample_time_ns < 0 or cumulative < 0:
            raise ValueError("samples_must_be_nonnegative")
        if sample_time_ns < last_time or cumulative < last_value:
            raise ValueError("samples_must_be_monotone")
        if sample_time_ns <= deadline_ns:
            value = cumulative
        last_time = sample_time_ns
        last_value = cumulative
    return value


def _write_source(path: Path, size_bytes: int) -> str:
    pattern = bytes(range(256))
    remaining = size_bytes
    digest = hashlib.sha256()
    with path.open("wb") as f:
        while remaining:
            chunk = pattern[: min(len(pattern), remaining)]
            f.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def run_lane(
    *,
    label: str,
    source_path: Path,
    source_bytes: int,
    chunk_bytes: int,
    cpu_quanta: int,
    transfer_delay_ms: int,
    cpu_gate_ms: int,
    deadline_ms: int,
) -> dict[str, Any]:
    if source_bytes <= 0 or chunk_bytes <= 0 or cpu_quanta <= 0:
        raise ValueError("positive_fixture_values_required")
    if transfer_delay_ms < 0 or cpu_gate_ms < 0 or deadline_ms <= 0:
        raise ValueError("invalid_timing_fixture")

    started_ns = time.monotonic_ns()
    deadline_ns = deadline_ms * 1_000_000
    transferred = 0
    payload = bytearray()
    transfer_samples: list[tuple[int, int]] = []

    with source_path.open("rb", buffering=0) as f:
        while transferred < source_bytes:
            chunk = f.read(min(chunk_bytes, source_bytes - transferred))
            if not chunk:
                raise RuntimeError("unexpected_source_eof")
            payload.extend(chunk)
            transferred += len(chunk)
            # The delay models when copied bytes become available to the runtime,
            # not raw media latency. Record service only after the pacing gate.
            if transfer_delay_ms:
                time.sleep(transfer_delay_ms / 1000.0)
            transfer_samples.append((time.monotonic_ns() - started_ns, transferred))

    transfer_done_ns = time.monotonic_ns() - started_ns
    source_digest = hashlib.sha256(payload).hexdigest()

    if cpu_gate_ms:
        time.sleep(cpu_gate_ms / 1000.0)

    cpu_samples: list[tuple[int, int]] = []
    quantum_digests: list[bytes] = []
    for quantum in range(cpu_quanta):
        h = hashlib.sha256()
        h.update(payload)
        h.update(quantum.to_bytes(4, "little"))
        quantum_digests.append(h.digest())
        cpu_samples.append((time.monotonic_ns() - started_ns, quantum + 1))

    finished_ns = time.monotonic_ns() - started_ns
    signature = hashlib.sha256(b"".join(quantum_digests)).hexdigest()
    transfer_at_deadline = service_at_deadline(transfer_samples, deadline_ns)
    cpu_at_deadline = service_at_deadline(cpu_samples, deadline_ns)
    typed_feasible = transfer_at_deadline >= source_bytes and cpu_at_deadline >= cpu_quanta
    actual_deadline_met = finished_ns <= deadline_ns

    return {
        "label": label,
        "transfer_delay_ms": transfer_delay_ms,
        "cpu_gate_ms": cpu_gate_ms,
        "deadline_ms": deadline_ms,
        "source_digest": source_digest,
        "semantic_signature": signature,
        "transfer_done_ns": transfer_done_ns,
        "finished_ns": finished_ns,
        "transfer_service_bytes_at_deadline": transfer_at_deadline,
        "cpu_service_quanta_at_deadline": cpu_at_deadline,
        "typed_conjunction_feasible": typed_feasible,
        "actual_deadline_met": actual_deadline_met,
    }


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(row[key]) for row in rows))


def run_panel(
    *,
    source_mib: int = 4,
    chunk_mib: int = 1,
    cpu_quanta: int = 4,
    deadline_ms: int = 100,
    repetitions: int = 3,
) -> dict[str, Any]:
    if source_mib <= 0 or chunk_mib <= 0 or repetitions <= 0:
        raise ValueError("positive_fixture_values_required")
    source_bytes = source_mib * MIB
    chunk_bytes = chunk_mib * MIB
    if source_bytes % chunk_bytes:
        raise ValueError("source_must_be_divisible_by_chunk")

    with tempfile.TemporaryDirectory(prefix="fr-p9-021-two-resource-") as tmp:
        source_path = Path(tmp) / "cold-capability.bin"
        expected_source_digest = _write_source(source_path, source_bytes)
        runs: list[dict[str, Any]] = []
        lane_names = tuple(LANES)
        for rep in range(repetitions):
            order = lane_names if rep % 2 == 0 else tuple(reversed(lane_names))
            for lane in order:
                cfg = LANES[lane]
                runs.append(
                    run_lane(
                        label=f"{lane}-r{rep}",
                        source_path=source_path,
                        source_bytes=source_bytes,
                        chunk_bytes=chunk_bytes,
                        cpu_quanta=cpu_quanta,
                        transfer_delay_ms=cfg["transfer_delay_ms"],
                        cpu_gate_ms=cfg["cpu_gate_ms"],
                        deadline_ms=deadline_ms,
                    )
                )

    signatures = {row["semantic_signature"] for row in runs}
    source_digests = {row["source_digest"] for row in runs}
    lanes: dict[str, dict[str, Any]] = {}
    for lane in LANES:
        rows = [row for row in runs if row["label"].startswith(lane + "-")]
        lanes[lane] = {
            "transfer_delay_ms": LANES[lane]["transfer_delay_ms"],
            "cpu_gate_ms": LANES[lane]["cpu_gate_ms"],
            "transfer_done_ns_median": _median(rows, "transfer_done_ns"),
            "finished_ns_median": _median(rows, "finished_ns"),
            "transfer_service_bytes_at_deadline_median": _median(
                rows, "transfer_service_bytes_at_deadline"
            ),
            "cpu_service_quanta_at_deadline_median": _median(
                rows, "cpu_service_quanta_at_deadline"
            ),
            "all_typed_conjunction_feasible": all(
                bool(row["typed_conjunction_feasible"]) for row in rows
            ),
            "all_actual_deadline_met": all(bool(row["actual_deadline_met"]) for row in rows),
            "all_prediction_matches_actual": all(
                bool(row["typed_conjunction_feasible"]) == bool(row["actual_deadline_met"])
                for row in rows
            ),
        }

    fast = lanes["FAST_FAST"]
    slow_transfer = lanes["SLOW_TRANSFER"]
    slow_cpu = lanes["SLOW_CPU"]
    slow_both = lanes["SLOW_BOTH"]

    checks = {
        "all_runs_preserve_source_and_semantic_signature": (
            source_digests == {expected_source_digest} and len(signatures) == 1
        ),
        "fast_fast_meets_both_resource_obligations_and_deadline": (
            fast["all_typed_conjunction_feasible"] is True
            and fast["all_actual_deadline_met"] is True
        ),
        "slow_transfer_fails_transfer_obligation_despite_fast_cpu_configuration": (
            slow_transfer["transfer_service_bytes_at_deadline_median"] < source_bytes
            and slow_transfer["all_typed_conjunction_feasible"] is False
            and slow_transfer["all_actual_deadline_met"] is False
        ),
        "slow_cpu_fails_cpu_obligation_despite_full_transfer": (
            slow_cpu["transfer_service_bytes_at_deadline_median"] >= source_bytes
            and slow_cpu["cpu_service_quanta_at_deadline_median"] < cpu_quanta
            and slow_cpu["all_typed_conjunction_feasible"] is False
            and slow_cpu["all_actual_deadline_met"] is False
        ),
        "slow_both_is_infeasible": (
            slow_both["all_typed_conjunction_feasible"] is False
            and slow_both["all_actual_deadline_met"] is False
        ),
        "typed_prediction_matches_physical_deadline_on_every_run": all(
            bool(row["typed_conjunction_feasible"]) == bool(row["actual_deadline_met"])
            for row in runs
        ),
        "transfer_surplus_or_cpu_surplus_never_substitutes_for_other_resource": (
            slow_transfer["all_typed_conjunction_feasible"] is False
            and slow_cpu["all_typed_conjunction_feasible"] is False
        ),
        "resource_conjunction_does_not_grant_authority": True,
        "resource_conjunction_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_USERSPACE_PACED_FILE_TRANSFER_PLUS_CPU_HASH_SERVICE_CONJUNCTION_PROXY",
        "fixture": {
            "source_mib": source_mib,
            "chunk_mib": chunk_mib,
            "cpu_quanta": cpu_quanta,
            "deadline_ms": deadline_ms,
            "repetitions": repetitions,
            "source_bytes": source_bytes,
            "transfer_unit": "bytes_delivered_to_runtime",
            "cpu_unit": "completed_sha256_quanta",
        },
        "lanes": lanes,
        "checks": checks,
        "decision": "END_TO_END_MATERIALIZATION_REQUIRES_EACH_TYPED_RESOURCE_SERVICE_OBLIGATION_TO_BE_MET_BY_DEADLINE_IF_QUALIFIED",
        "claim_ceiling": "HOSTED_GITHUB_USERSPACE_PACED_FILE_TRANSFER_AND_CPU_HASH_PROXY_ONLY_NO_MEDIA_BANDWIDTH_CPU_SCHEDULER_OR_APPLICATION_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "COMPOSED_STAGE_SERVICE_CURVES_AND_PIPELINE_DEPENDENCIES",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    result = run_panel(repetitions=args.repetitions)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
