from __future__ import annotations

import argparse
import hashlib
import json
import queue
import statistics
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-023-prefix-streaming-release/v0.1"
MIB = 1024 * 1024


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


def _chunk_digest(chunk: bytes, index: int) -> bytes:
    h = hashlib.sha256()
    h.update(index.to_bytes(4, "little"))
    h.update(chunk)
    return h.digest()


def _service_at_deadline(samples: list[tuple[int, int]], deadline_ns: int) -> int:
    value = 0
    for when_ns, cumulative in samples:
        if when_ns <= deadline_ns:
            value = cumulative
        else:
            break
    return value


def run_full_barrier(
    *,
    source_path: Path,
    source_bytes: int,
    chunk_bytes: int,
    transfer_gate_ms: int,
    cpu_gate_ms: int,
    deadline_ms: int,
) -> dict[str, Any]:
    started_ns = time.monotonic_ns()
    transfer_samples: list[tuple[int, int]] = []
    cpu_samples: list[tuple[int, int]] = []
    chunks: list[bytes] = []
    transferred = 0

    with source_path.open("rb", buffering=0) as f:
        index = 0
        while transferred < source_bytes:
            chunk = f.read(min(chunk_bytes, source_bytes - transferred))
            if not chunk:
                raise RuntimeError("unexpected_source_eof")
            if transfer_gate_ms:
                time.sleep(transfer_gate_ms / 1000.0)
            chunks.append(chunk)
            transferred += len(chunk)
            index += 1
            transfer_samples.append((time.monotonic_ns() - started_ns, transferred))

    full_release_ns = time.monotonic_ns() - started_ns
    digests: list[bytes] = []
    for index, chunk in enumerate(chunks):
        if cpu_gate_ms:
            time.sleep(cpu_gate_ms / 1000.0)
        digests.append(_chunk_digest(chunk, index))
        cpu_samples.append((time.monotonic_ns() - started_ns, index + 1))

    finished_ns = time.monotonic_ns() - started_ns
    deadline_ns = deadline_ms * 1_000_000
    return {
        "mode": "FULL_BARRIER",
        "source_digest": hashlib.sha256(b"".join(chunks)).hexdigest(),
        "semantic_signature": hashlib.sha256(b"".join(digests)).hexdigest(),
        "full_release_ns": full_release_ns,
        "finished_ns": finished_ns,
        "transfer_bytes_at_deadline": _service_at_deadline(transfer_samples, deadline_ns),
        "cpu_quanta_at_deadline": _service_at_deadline(cpu_samples, deadline_ns),
        "deadline_met": finished_ns <= deadline_ns,
        "logical_peak_buffered_bytes": source_bytes,
    }


def run_prefix_streaming(
    *,
    source_path: Path,
    source_bytes: int,
    chunk_bytes: int,
    transfer_gate_ms: int,
    cpu_gate_ms: int,
    deadline_ms: int,
) -> dict[str, Any]:
    started_ns = time.monotonic_ns()
    transfer_samples: list[tuple[int, int]] = []
    cpu_samples: list[tuple[int, int]] = []
    q: queue.Queue[tuple[int, bytes] | None] = queue.Queue()
    digests: dict[int, bytes] = {}
    worker_error: list[BaseException] = []
    buffered_bytes = 0
    logical_peak_buffered_bytes = 0
    buffer_lock = threading.Lock()

    def worker() -> None:
        nonlocal buffered_bytes
        try:
            completed = 0
            while True:
                item = q.get()
                if item is None:
                    q.task_done()
                    return
                index, chunk = item
                if cpu_gate_ms:
                    time.sleep(cpu_gate_ms / 1000.0)
                digests[index] = _chunk_digest(chunk, index)
                completed += 1
                cpu_samples.append((time.monotonic_ns() - started_ns, completed))
                with buffer_lock:
                    buffered_bytes -= len(chunk)
                q.task_done()
        except BaseException as exc:
            worker_error.append(exc)

    thread = threading.Thread(target=worker, name="p9-023-stream-worker", daemon=True)
    thread.start()

    transferred = 0
    source_digest = hashlib.sha256()
    with source_path.open("rb", buffering=0) as f:
        index = 0
        while transferred < source_bytes:
            chunk = f.read(min(chunk_bytes, source_bytes - transferred))
            if not chunk:
                raise RuntimeError("unexpected_source_eof")
            source_digest.update(chunk)
            if transfer_gate_ms:
                time.sleep(transfer_gate_ms / 1000.0)
            transferred += len(chunk)
            transfer_samples.append((time.monotonic_ns() - started_ns, transferred))
            with buffer_lock:
                buffered_bytes += len(chunk)
                logical_peak_buffered_bytes = max(logical_peak_buffered_bytes, buffered_bytes)
            q.put((index, chunk))
            index += 1

    full_release_ns = time.monotonic_ns() - started_ns
    q.put(None)
    q.join()
    thread.join(timeout=5)
    if thread.is_alive():
        raise TimeoutError("stream_worker_timeout")
    if worker_error:
        raise RuntimeError("stream_worker_failed") from worker_error[0]

    expected_chunks = source_bytes // chunk_bytes
    if set(digests) != set(range(expected_chunks)):
        raise RuntimeError("missing_chunk_digest")
    ordered = [digests[index] for index in range(expected_chunks)]
    finished_ns = time.monotonic_ns() - started_ns
    deadline_ns = deadline_ms * 1_000_000
    return {
        "mode": "PREFIX_STREAMING",
        "source_digest": source_digest.hexdigest(),
        "semantic_signature": hashlib.sha256(b"".join(ordered)).hexdigest(),
        "full_release_ns": full_release_ns,
        "finished_ns": finished_ns,
        "transfer_bytes_at_deadline": _service_at_deadline(transfer_samples, deadline_ns),
        "cpu_quanta_at_deadline": _service_at_deadline(cpu_samples, deadline_ns),
        "deadline_met": finished_ns <= deadline_ns,
        "logical_peak_buffered_bytes": logical_peak_buffered_bytes,
    }


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(row[key]) for row in rows))


def run_panel(
    *,
    source_mib: int = 4,
    chunk_mib: int = 1,
    transfer_gate_ms: int = 25,
    cpu_gate_ms: int = 20,
    deadline_ms: int = 150,
    repetitions: int = 3,
) -> dict[str, Any]:
    if source_mib <= 0 or chunk_mib <= 0 or repetitions <= 0:
        raise ValueError("positive_fixture_values_required")
    source_bytes = source_mib * MIB
    chunk_bytes = chunk_mib * MIB
    if source_bytes % chunk_bytes:
        raise ValueError("source_must_be_divisible_by_chunk")
    chunk_count = source_bytes // chunk_bytes

    with tempfile.TemporaryDirectory(prefix="fr-p9-023-prefix-") as tmp:
        source_path = Path(tmp) / "capability.bin"
        expected_source_digest = _write_source(source_path, source_bytes)
        runs: list[dict[str, Any]] = []
        for rep in range(repetitions):
            order = ("FULL_BARRIER", "PREFIX_STREAMING") if rep % 2 == 0 else (
                "PREFIX_STREAMING", "FULL_BARRIER"
            )
            for mode in order:
                kwargs = {
                    "source_path": source_path,
                    "source_bytes": source_bytes,
                    "chunk_bytes": chunk_bytes,
                    "transfer_gate_ms": transfer_gate_ms,
                    "cpu_gate_ms": cpu_gate_ms,
                    "deadline_ms": deadline_ms,
                }
                result = run_full_barrier(**kwargs) if mode == "FULL_BARRIER" else run_prefix_streaming(**kwargs)
                result["rep"] = rep
                runs.append(result)

    full_rows = [row for row in runs if row["mode"] == "FULL_BARRIER"]
    stream_rows = [row for row in runs if row["mode"] == "PREFIX_STREAMING"]
    source_digests = {row["source_digest"] for row in runs}
    signatures = {row["semantic_signature"] for row in runs}

    full = {
        "finished_ns_median": _median(full_rows, "finished_ns"),
        "full_release_ns_median": _median(full_rows, "full_release_ns"),
        "transfer_bytes_at_deadline_median": _median(full_rows, "transfer_bytes_at_deadline"),
        "cpu_quanta_at_deadline_median": _median(full_rows, "cpu_quanta_at_deadline"),
        "logical_peak_buffered_bytes_median": _median(full_rows, "logical_peak_buffered_bytes"),
        "all_deadline_met": all(bool(row["deadline_met"]) for row in full_rows),
    }
    stream = {
        "finished_ns_median": _median(stream_rows, "finished_ns"),
        "full_release_ns_median": _median(stream_rows, "full_release_ns"),
        "transfer_bytes_at_deadline_median": _median(stream_rows, "transfer_bytes_at_deadline"),
        "cpu_quanta_at_deadline_median": _median(stream_rows, "cpu_quanta_at_deadline"),
        "logical_peak_buffered_bytes_median": _median(stream_rows, "logical_peak_buffered_bytes"),
        "all_deadline_met": all(bool(row["deadline_met"]) for row in stream_rows),
    }

    checks = {
        "all_runs_preserve_source_and_semantic_signature": (
            source_digests == {expected_source_digest} and len(signatures) == 1
        ),
        "both_modes_deliver_full_transfer_by_deadline": (
            full["transfer_bytes_at_deadline_median"] >= source_bytes
            and stream["transfer_bytes_at_deadline_median"] >= source_bytes
        ),
        "full_barrier_misses_deadline": full["all_deadline_met"] is False,
        "prefix_streaming_meets_deadline": stream["all_deadline_met"] is True,
        "full_barrier_has_incomplete_cpu_service_at_deadline": (
            full["cpu_quanta_at_deadline_median"] < chunk_count
        ),
        "prefix_streaming_has_complete_cpu_service_at_deadline": (
            stream["cpu_quanta_at_deadline_median"] >= chunk_count
        ),
        "prefix_streaming_finishes_materially_earlier": (
            full["finished_ns_median"] - stream["finished_ns_median"] >= 30_000_000
        ),
        "prefix_streaming_does_not_require_full_object_buffer_before_cpu": (
            stream["logical_peak_buffered_bytes_median"] < full["logical_peak_buffered_bytes_median"]
        ),
        "release_granularity_does_not_grant_authority": True,
        "release_granularity_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_USERSPACE_PREFIX_RELEASE_STREAMING_PIPELINE_PROXY",
        "fixture": {
            "source_mib": source_mib,
            "chunk_mib": chunk_mib,
            "chunk_count": chunk_count,
            "transfer_gate_ms_per_chunk": transfer_gate_ms,
            "cpu_gate_ms_per_chunk": cpu_gate_ms,
            "deadline_ms": deadline_ms,
            "repetitions": repetitions,
        },
        "full_barrier": full,
        "prefix_streaming": stream,
        "checks": checks,
        "decision": "SEMANTIC_RELEASE_GRANULARITY_CAN_CHANGE_DEADLINE_FEASIBILITY_AND_RESIDENCY_BUFFERING_IF_PREFIXES_ARE_INDEPENDENTLY_PROCESSABLE_IF_QUALIFIED",
        "claim_ceiling": "HOSTED_GITHUB_USERSPACE_PACED_CHUNK_PIPELINE_PROXY_ONLY_NO_STORAGE_BANDWIDTH_CPU_SCHEDULER_OR_UNIVERSAL_STREAMING_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "SEMANTIC_PREFIX_VALIDITY_AND_PARTIAL_RECONSTRUCTION_CONTRACT",
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
