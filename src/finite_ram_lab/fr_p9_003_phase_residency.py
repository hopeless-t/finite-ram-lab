from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-003-phase-residency/v0.1"


@dataclass(frozen=True)
class PhaseCost:
    policy: str
    phase_gap_seconds: float
    resident_byte_seconds: float
    requested_transfer_bytes: int
    resume_latency_ns: int


def dominates(a: PhaseCost, b: PhaseCost) -> bool:
    no_worse = (
        a.resident_byte_seconds <= b.resident_byte_seconds
        and a.requested_transfer_bytes <= b.requested_transfer_bytes
        and a.resume_latency_ns <= b.resume_latency_ns
    )
    strictly_better = (
        a.resident_byte_seconds < b.resident_byte_seconds
        or a.requested_transfer_bytes < b.requested_transfer_bytes
        or a.resume_latency_ns < b.resume_latency_ns
    )
    return no_worse and strictly_better


def phase_vectors(
    *,
    payload_bytes: int,
    phase_gap_seconds: float,
    warm_resume_latency_ns: int,
    fault_resume_latency_ns: int,
) -> tuple[PhaseCost, PhaseCost]:
    if payload_bytes <= 0:
        raise ValueError("payload_bytes_must_be_positive")
    if phase_gap_seconds <= 0:
        raise ValueError("phase_gap_seconds_must_be_positive")
    if warm_resume_latency_ns < 0 or fault_resume_latency_ns < 0:
        raise ValueError("latency_must_be_nonnegative")

    warm = PhaseCost(
        policy="KEEP_WARM",
        phase_gap_seconds=phase_gap_seconds,
        resident_byte_seconds=payload_bytes * phase_gap_seconds,
        requested_transfer_bytes=0,
        resume_latency_ns=warm_resume_latency_ns,
    )
    fault = PhaseCost(
        policy="FAULT_IN",
        phase_gap_seconds=phase_gap_seconds,
        resident_byte_seconds=0.0,
        requested_transfer_bytes=payload_bytes,
        resume_latency_ns=fault_resume_latency_ns,
    )
    return warm, fault


def scalar_break_even_gap_seconds(
    *,
    payload_bytes: int,
    warm_resume_latency_ns: int,
    fault_resume_latency_ns: int,
    resident_byte_second_price: float,
    transfer_byte_price: float,
    latency_ns_price: float,
) -> float | None:
    """Return a scalarized crossover only when an external price vector exists.

    No price vector is inferred by the lab. A non-positive resident-byte-second
    price means there is no finite gap threshold under this scalarization.
    """

    if payload_bytes <= 0:
        raise ValueError("payload_bytes_must_be_positive")
    if resident_byte_second_price <= 0:
        return None
    if transfer_byte_price < 0 or latency_ns_price < 0:
        raise ValueError("prices_must_be_nonnegative")

    numerator = (
        transfer_byte_price * payload_bytes
        + latency_ns_price * (fault_resume_latency_ns - warm_resume_latency_ns)
    )
    if numerator <= 0:
        return 0.0
    return numerator / (resident_byte_second_price * payload_bytes)


def _payload_chunk() -> bytes:
    seed = b"catfood-lab-fr-p9-003-phase-residency|"
    return (seed * ((1024 * 1024 // len(seed)) + 1))[: 1024 * 1024]


def _write_payload(path: Path, payload_bytes: int) -> str:
    chunk = _payload_chunk()
    digest = hashlib.sha256()
    remaining = payload_bytes
    with path.open("wb") as handle:
        while remaining:
            piece = chunk[: min(len(chunk), remaining)]
            handle.write(piece)
            digest.update(piece)
            remaining -= len(piece)
        handle.flush()
        os.fsync(handle.fileno())
    return digest.hexdigest()


def _best_effort_dontneed(fd: int) -> bool:
    if not hasattr(os, "posix_fadvise") or not hasattr(os, "POSIX_FADV_DONTNEED"):
        return False
    try:
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    except OSError:
        return False
    return True


def _hash_bytes(payload: bytes) -> tuple[str, int]:
    start = time.perf_counter_ns()
    digest = hashlib.sha256(payload).hexdigest()
    return digest, time.perf_counter_ns() - start


def _fault_read_and_hash(path: Path) -> tuple[str, int, bool]:
    with path.open("rb", buffering=0) as handle:
        dropped = _best_effort_dontneed(handle.fileno())
        os.lseek(handle.fileno(), 0, os.SEEK_SET)
        start = time.perf_counter_ns()
        payload = handle.read()
        digest = hashlib.sha256(payload).hexdigest()
        elapsed = time.perf_counter_ns() - start
    return digest, elapsed, dropped


def run_hosted_proxy(
    *,
    payload_bytes: int = 8 * 1024 * 1024,
    repetitions: int = 6,
    gaps_seconds: tuple[float, ...] = (0.1, 1.0, 10.0),
) -> dict[str, Any]:
    if repetitions < 3:
        raise ValueError("repetitions_must_be_at_least_three")

    with tempfile.TemporaryDirectory(prefix="fr-p9-003-") as tmp:
        path = Path(tmp) / "capability.bin"
        expected_digest = _write_payload(path, payload_bytes)
        warm_payload = path.read_bytes()
        if hashlib.sha256(warm_payload).hexdigest() != expected_digest:
            raise RuntimeError("warm_payload_digest_mismatch")

        warm_samples: list[int] = []
        fault_samples: list[int] = []
        fault_digests: list[str] = []
        dontneed_successes = 0

        for index in range(repetitions):
            # Alternate ordering to reduce monotonic run-order bias.
            if index % 2 == 0:
                warm_digest, warm_ns = _hash_bytes(warm_payload)
                fault_digest, fault_ns, dropped = _fault_read_and_hash(path)
            else:
                fault_digest, fault_ns, dropped = _fault_read_and_hash(path)
                warm_digest, warm_ns = _hash_bytes(warm_payload)

            if warm_digest != expected_digest:
                raise RuntimeError("warm_digest_mismatch")
            if fault_digest != expected_digest:
                raise RuntimeError("fault_digest_mismatch")

            warm_samples.append(warm_ns)
            fault_samples.append(fault_ns)
            fault_digests.append(fault_digest)
            dontneed_successes += int(dropped)

        warm_median = int(statistics.median(warm_samples))
        fault_median = int(statistics.median(fault_samples))

        rows: list[dict[str, Any]] = []
        both_nondominated = True
        for gap in gaps_seconds:
            warm, fault = phase_vectors(
                payload_bytes=payload_bytes,
                phase_gap_seconds=gap,
                warm_resume_latency_ns=warm_median,
                fault_resume_latency_ns=fault_median,
            )
            warm_dominates = dominates(warm, fault)
            fault_dominates = dominates(fault, warm)
            both_nondominated = both_nondominated and not warm_dominates and not fault_dominates
            rows.append(
                {
                    "phase_gap_seconds": gap,
                    "KEEP_WARM": asdict(warm),
                    "FAULT_IN": asdict(fault),
                    "warm_dominates": warm_dominates,
                    "fault_dominates": fault_dominates,
                }
            )

    checks = {
        "all_warm_digests_match": True,
        "all_fault_digests_match": len(set(fault_digests)) == 1 and fault_digests[0] == expected_digest,
        "warm_has_zero_requested_transfer_bytes": all(
            row["KEEP_WARM"]["requested_transfer_bytes"] == 0 for row in rows
        ),
        "fault_has_zero_gap_resident_byte_seconds": all(
            row["FAULT_IN"]["resident_byte_seconds"] == 0 for row in rows
        ),
        "typed_frontier_keeps_both_policies_without_external_prices": both_nondominated,
        "no_scalar_price_vector_is_inferred": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_FILE_FAULT_PROXY_PLUS_TYPED_PHASE_RESIDENCY_FRONTIER",
        "probe": {
            "payload_bytes": payload_bytes,
            "repetitions": repetitions,
            "warm_resume_latency_ns_samples": warm_samples,
            "fault_resume_latency_ns_samples": fault_samples,
            "warm_resume_latency_ns_median": warm_median,
            "fault_resume_latency_ns_median": fault_median,
            "posix_fadvise_dontneed_successes": dontneed_successes,
            "expected_digest": expected_digest,
        },
        "phase_frontier": rows,
        "checks": checks,
        "decision": (
            "KEEP_WARM_AND_FAULT_IN_REMAIN_TYPED_PARETO_ALTERNATIVES_UNTIL_AN_EXTERNAL_PRICE_OR_HARD_CONSTRAINT_IS_SUPPLIED"
        ),
        "scalarization_rule": (
            "if explicit prices are supplied, solve gap* = [p_transfer*B + p_latency*(L_fault-L_warm)] / (p_resident*B); otherwise scalar_gain=null"
        ),
        "invariants": [
            "semantic temperature != physical residency",
            "warm residency trades byte-time for lower requested transfer",
            "fault-in trades transfer/resume work for lower gap residency",
            "hosted file-read latency is a proxy, not a universal SSD law",
            "no external price vector => no universal warm/cold winner",
        ],
        "authority_effect": "NONE",
        "scalar_gain": None,
        "next_falsifier": (
            "add repeated phase transitions and capability reuse counts; test parallelism and cache-sharing taxes before admitting KEEP_WARM"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_FILE_READ_PROXY_AND_TYPED_COST_FRONTIER_ONLY_NO_UNIVERSAL_STORAGE_OR_HOST_THRESHOLD_CLAIM"
        ),
    }


def run_synthetic_panel() -> dict[str, Any]:
    rows = []
    for gap in (0.1, 1.0, 10.0):
        warm, fault = phase_vectors(
            payload_bytes=8 * 1024 * 1024,
            phase_gap_seconds=gap,
            warm_resume_latency_ns=1_000_000,
            fault_resume_latency_ns=5_000_000,
        )
        rows.append(
            {
                "gap": gap,
                "warm": asdict(warm),
                "fault": asdict(fault),
                "warm_dominates": dominates(warm, fault),
                "fault_dominates": dominates(fault, warm),
            }
        )
    checks = {
        "both_policies_nondominated": all(
            not row["warm_dominates"] and not row["fault_dominates"] for row in rows
        ),
        "no_default_scalarization": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_TYPED_PHASE_RESIDENCY_FRONTIER",
        "rows": rows,
        "checks": checks,
        "scalar_gain": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--repetitions", type=int, default=6)
    args = parser.parse_args()

    if args.physical:
        result = run_hosted_proxy(
            payload_bytes=args.payload_mib * 1024 * 1024,
            repetitions=args.repetitions,
        )
    else:
        result = run_synthetic_panel()

    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
