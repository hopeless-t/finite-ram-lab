from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable


ARMS = ("pip_source", "pip_wheel", "wheel_extract")
WORKLOAD_CODE = r'''
import hashlib, json, random, resource
from finite_ram_lab.sim import generate_trace, lru_faults, opt_faults
rng = random.Random(20261012)
trace = generate_trace("shifting_hotset", rng, 12000, 257, 41)
payload = {
    "trace_sha256": hashlib.sha256(bytes((x % 256 for x in trace))).hexdigest(),
    "lru_faults": lru_faults(trace, 41),
    "opt_faults": opt_faults(trace, 41),
    "trace_len": len(trace),
    "ru_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
canonical = {k: v for k, v in payload.items() if k != "ru_maxrss_kib"}
payload["semantic_sha256"] = hashlib.sha256(
    json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(payload, sort_keys=True))
'''.strip()


def meminfo() -> dict[str, int]:
    result: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, raw = line.split(":", 1)
            token = raw.strip().split()[0]
            result[key] = int(token)
    except (OSError, ValueError, IndexError):
        pass
    return result


def tree_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return 0
    for base, _dirs, files in os.walk(root):
        for name in files:
            try:
                total += (Path(base) / name).stat().st_size
            except OSError:
                pass
    return total


def _rss_kib(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return 0
    return 0


def run_measured(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    poll_s: float = 0.005,
) -> dict[str, Any]:
    before = meminfo()
    started = time.perf_counter_ns()
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    peak_rss_kib = 0
    while proc.poll() is None:
        peak_rss_kib = max(peak_rss_kib, _rss_kib(proc.pid))
        time.sleep(poll_s)
    stdout, stderr = proc.communicate()
    peak_rss_kib = max(peak_rss_kib, _rss_kib(proc.pid))
    elapsed_ns = time.perf_counter_ns() - started
    after = meminfo()
    return {
        "returncode": proc.returncode,
        "elapsed_ns": elapsed_ns,
        "peak_rss_kib": peak_rss_kib,
        "stdout": stdout,
        "stderr": stderr,
        "mem_available_before_kib": before.get("MemAvailable"),
        "mem_available_after_kib": after.get("MemAvailable"),
        "cached_before_kib": before.get("Cached"),
        "cached_after_kib": after.get("Cached"),
    }


def schedule(blocks: int, seed: int) -> list[tuple[int, int, str]]:
    if blocks <= 0:
        raise ValueError("blocks must be positive")
    rows: list[tuple[int, int, str]] = []
    for block in range(blocks):
        arms = list(ARMS)
        random.Random(seed + block * 1009).shuffle(arms)
        rows.extend((block, order, arm) for order, arm in enumerate(arms))
    return rows


def build_wheel(repo: Path, artifact_dir: Path) -> tuple[Path, dict[str, Any]]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result = run_measured(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--no-cache-dir",
            "-w",
            str(artifact_dir),
        ],
        cwd=repo,
    )
    if result["returncode"] != 0:
        raise RuntimeError(f"wheel build failed: {result['stderr'][-2000:]}")
    wheels = sorted(artifact_dir.glob("finite_ram_lab-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one finite-ram-lab wheel, got {wheels}")
    return wheels[0], result


def reconstruct(
    arm: str,
    *,
    repo: Path,
    wheel: Path,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    if arm == "wheel_extract":
        before = meminfo()
        started = time.perf_counter_ns()
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(target)
        elapsed_ns = time.perf_counter_ns() - started
        after = meminfo()
        result: dict[str, Any] = {
            "returncode": 0,
            "elapsed_ns": elapsed_ns,
            "peak_rss_kib": None,
            "stdout": "",
            "stderr": "",
            "mem_available_before_kib": before.get("MemAvailable"),
            "mem_available_after_kib": after.get("MemAvailable"),
            "cached_before_kib": before.get("Cached"),
            "cached_after_kib": after.get("Cached"),
        }
    else:
        source = "." if arm == "pip_source" else str(wheel)
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-cache-dir",
            "--target",
            str(target),
        ]
        if arm == "pip_source":
            cmd.append("--no-build-isolation")
        cmd.append(source)
        result = run_measured(cmd, cwd=repo)
    result["runtime_bytes"] = tree_bytes(target)
    return result


def run_workload(repo: Path, target: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(target)
    result = run_measured(
        [sys.executable, "-c", WORKLOAD_CODE],
        cwd=repo,
        env=env,
    )
    if result["returncode"] != 0:
        raise RuntimeError(f"workload failed: {result['stderr'][-2000:]}")
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("workload produced no JSON")
    result["payload"] = json.loads(lines[-1])
    return result


def discard(target: Path) -> dict[str, Any]:
    before_bytes = tree_bytes(target)
    started = time.perf_counter_ns()
    shutil.rmtree(target)
    elapsed_ns = time.perf_counter_ns() - started
    return {
        "elapsed_ns": elapsed_ns,
        "bytes_before": before_bytes,
        "bytes_after": tree_bytes(target),
        "target_exists_after": target.exists(),
    }


def _median(rows: Iterable[dict[str, Any]], key: str) -> float:
    vals = [float(row[key]) for row in rows if row.get(key) is not None]
    return float(statistics.median(vals)) if vals else 0.0


def summarize(trials: list[dict[str, Any]]) -> dict[str, Any]:
    if not trials:
        raise ValueError("no trials")
    semantic = {row["workload"]["payload"]["semantic_sha256"] for row in trials}
    by_arm: dict[str, Any] = {}
    for arm in ARMS:
        rows = [row for row in trials if row["arm"] == arm]
        if not rows:
            continue
        by_arm[arm] = {
            "n": len(rows),
            "median_reconstruct_ms": _median(
                ({"v": r["reconstruct"]["elapsed_ns"] / 1e6} for r in rows), "v"
            ),
            "median_reconstruct_peak_rss_kib": _median(
                ({"v": r["reconstruct"].get("peak_rss_kib")} for r in rows), "v"
            ),
            "median_runtime_bytes": _median(
                ({"v": r["reconstruct"]["runtime_bytes"]} for r in rows), "v"
            ),
            "median_workload_ms": _median(
                ({"v": r["workload"]["elapsed_ns"] / 1e6} for r in rows), "v"
            ),
            "median_workload_ru_maxrss_kib": _median(
                ({"v": r["workload"]["payload"]["ru_maxrss_kib"]} for r in rows), "v"
            ),
            "median_discard_ms": _median(
                ({"v": r["discard"]["elapsed_ns"] / 1e6} for r in rows), "v"
            ),
            "residual_bytes_max": max(int(r["discard"]["bytes_after"]) for r in rows),
            "semantic_hashes": sorted(
                {r["workload"]["payload"]["semantic_sha256"] for r in rows}
            ),
        }
    baseline = by_arm.get("pip_source", {}).get("median_reconstruct_ms")
    if baseline:
        for metrics in by_arm.values():
            value = metrics["median_reconstruct_ms"]
            metrics["reconstruct_speedup_vs_pip_source"] = baseline / value if value else None
    return {
        "trial_count": len(trials),
        "semantic_parity": len(semantic) == 1,
        "semantic_hashes": sorted(semantic),
        "all_discarded_cleanly": all(
            r["discard"]["bytes_after"] == 0 and not r["discard"]["target_exists_after"]
            for r in trials
        ),
        "arms": by_arm,
    }


def run_experiment(repo: Path, out: Path, *, blocks: int, seed: int) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    runtime_root = out / "runtime"
    artifacts = out / "artifacts"
    wheel, wheel_build = build_wheel(repo, artifacts)
    trials: list[dict[str, Any]] = []
    jsonl = out / "trials.jsonl"
    for block, order, arm in schedule(blocks, seed):
        target = runtime_root / f"b{block:03d}-o{order}-{arm}"
        rec = reconstruct(arm, repo=repo, wheel=wheel, target=target)
        if rec["returncode"] != 0:
            raise RuntimeError(f"reconstruct failed ({arm}): {rec['stderr'][-2000:]}")
        workload = run_workload(repo, target)
        clean = discard(target)
        row = {
            "block": block,
            "order": order,
            "arm": arm,
            "reconstruct": rec,
            "workload": workload,
            "discard": clean,
        }
        trials.append(row)
        with jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    summary = summarize(trials)
    summary["experiment_id"] = "FRL-REINSTALL-001-PILOT-v1"
    summary["blocks"] = blocks
    summary["seed"] = seed
    summary["wheel"] = {
        "name": wheel.name,
        "bytes": wheel.stat().st_size,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "build_elapsed_ms": wheel_build["elapsed_ns"] / 1e6,
        "build_peak_rss_kib": wheel_build["peak_rss_kib"],
    }
    summary["cold_semantics"] = (
        "Fresh runtime directory per trial; host page cache is intentionally not globally dropped."
    )
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Finite RAM fast reinstall loop pilot")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--blocks", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261012)
    args = parser.parse_args()
    summary = run_experiment(
        Path(args.repo).resolve(),
        Path(args.out).resolve(),
        blocks=args.blocks,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
