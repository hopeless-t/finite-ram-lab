from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from .fast_reinstall_loop_v2 import build_wheel_isolated, sha256_file

ARMS = ("full_sha256", "epoch_identity")


def identity(path: Path) -> tuple[int, int, int, int, int]:
    st = path.stat()
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def make_epoch(path: Path) -> dict[str, Any]:
    return {
        "sha256": sha256_file(path),
        "identity": identity(path),
        "bytes": path.stat().st_size,
    }


def verify_full(path: Path, epoch: dict[str, Any]) -> bool:
    return sha256_file(path) == epoch["sha256"]


def verify_epoch(path: Path, epoch: dict[str, Any]) -> bool:
    return identity(path) == tuple(epoch["identity"])


def bench(path: Path, epoch: dict[str, Any], *, rounds: int, seed: int) -> dict[str, Any]:
    funcs = {"full_sha256": verify_full, "epoch_identity": verify_epoch}
    samples = {arm: [] for arm in ARMS}
    schedule: list[str] = []
    for block in range(rounds):
        arms = list(ARMS)
        random.Random(seed + block * 7919).shuffle(arms)
        schedule.extend(arms)
    for arm in schedule:
        t0 = time.perf_counter_ns()
        ok = funcs[arm](path, epoch)
        elapsed = time.perf_counter_ns() - t0
        if not ok:
            raise RuntimeError(f"verification unexpectedly failed for {arm}")
        samples[arm].append(elapsed)
    out: dict[str, Any] = {}
    for arm, ns in samples.items():
        ms = sorted(v / 1e6 for v in ns)
        out[arm] = {
            "n": len(ms),
            "median_ms": float(statistics.median(ms)),
            "p95_ms": float(ms[max(0, int(len(ms) * 0.95) - 1)]),
            "min_ms": float(ms[0]),
            "max_ms": float(ms[-1]),
        }
    out["epoch_identity"]["speedup_vs_full_sha256"] = (
        out["full_sha256"]["median_ms"] / out["epoch_identity"]["median_ms"]
    )
    return out


def mutation_probe(path: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="frl-epoch-mutation-") as td:
        copy = Path(td) / path.name
        shutil.copy2(path, copy)
        epoch = make_epoch(copy)
        before = copy.stat()
        with copy.open("r+b") as fh:
            head = fh.read(1)
            if not head:
                raise RuntimeError("empty artifact")
            fh.seek(0)
            fh.write(bytes([head[0] ^ 0x01]))
            fh.flush()
            os.fsync(fh.fileno())
        # Attempt to hide the ordinary content write by restoring mtime.
        os.utime(copy, ns=(before.st_atime_ns, before.st_mtime_ns))
        after_id = identity(copy)
        return {
            "same_size": copy.stat().st_size == before.st_size,
            "mtime_restored": copy.stat().st_mtime_ns == before.st_mtime_ns,
            "ctime_changed": copy.stat().st_ctime_ns != before.st_ctime_ns,
            "identity_changed": after_id != tuple(epoch["identity"]),
            "epoch_identity_detected": not verify_epoch(copy, epoch),
            "full_sha256_detected": not verify_full(copy, epoch),
        }


def run(repo: Path, out: Path, *, rounds: int, seed: int) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    wheel, build = build_wheel_isolated(repo, out / "artifacts")
    epoch = make_epoch(wheel)
    result = {
        "experiment_id": "FRL-REINSTALL-003-ARTIFACT-EPOCH-v1",
        "rounds_per_arm": rounds,
        "wheel": {
            "bytes": wheel.stat().st_size,
            "sha256": epoch["sha256"],
            "identity": list(epoch["identity"]),
        },
        "canonical_build_residue_delta_bytes": build["canonical_residue_delta_bytes"],
        "verification": bench(wheel, epoch, rounds=rounds, seed=seed),
        "mutation_probe": mutation_probe(wheel),
        "threat_model": (
            "Epoch identity is a local immutable-artifact optimization, not a replacement "
            "for cryptographic verification against a privileged or filesystem-level adversary."
        ),
    }
    (out / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--out", required=True)
    p.add_argument("--rounds", type=int, default=2000)
    p.add_argument("--seed", type=int, default=20261012)
    a = p.parse_args()
    print(json.dumps(run(Path(a.repo).resolve(), Path(a.out).resolve(), rounds=a.rounds, seed=a.seed), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
