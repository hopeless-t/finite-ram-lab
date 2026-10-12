from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

from .fast_reinstall_loop import WORKLOAD_CODE, run_measured, tree_bytes


ARMS = ("wheel_extract", "wheel_zipimport")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_wheel_isolated(repo: Path, artifact_dir: Path) -> tuple[Path, dict[str, Any]]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="frl-wheel-src-") as td:
        src_root = Path(td) / "source"
        src_root.mkdir()
        shutil.copy2(repo / "pyproject.toml", src_root / "pyproject.toml")
        shutil.copytree(
            repo / "src",
            src_root / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )
        before_repo = _generated_residue_bytes(repo)
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
            cwd=src_root,
        )
        after_repo = _generated_residue_bytes(repo)
    if result["returncode"] != 0:
        raise RuntimeError(f"isolated wheel build failed: {result['stderr'][-2000:]}")
    wheels = sorted(artifact_dir.glob("finite_ram_lab-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected one wheel, got {wheels}")
    result["canonical_residue_bytes_before"] = before_repo
    result["canonical_residue_bytes_after"] = after_repo
    result["canonical_residue_delta_bytes"] = after_repo - before_repo
    return wheels[0], result


def _generated_residue_bytes(repo: Path) -> int:
    total = 0
    candidates = [repo / "build"] + list((repo / "src").glob("*.egg-info"))
    for path in candidates:
        total += tree_bytes(path)
    return total


def schedule(blocks: int, seed: int) -> list[tuple[int, int, str]]:
    if blocks <= 0:
        raise ValueError("blocks must be positive")
    rows: list[tuple[int, int, str]] = []
    for block in range(blocks):
        arms = list(ARMS)
        random.Random(seed + 2029 * block).shuffle(arms)
        rows.extend((block, order, arm) for order, arm in enumerate(arms))
    return rows


def reconstruct(
    arm: str,
    *,
    wheel: Path,
    expected_sha256: str,
    target: Path,
) -> dict[str, Any]:
    if target.exists():
        shutil.rmtree(target)
    started = time.perf_counter_ns()
    digest = sha256_file(wheel)
    if digest != expected_sha256:
        raise RuntimeError("canonical wheel digest changed")
    target.mkdir(parents=True)
    if arm == "wheel_extract":
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(target)
        import_path = target
    elif arm == "wheel_zipimport":
        if not zipfile.is_zipfile(wheel):
            raise RuntimeError("canonical artifact is not a readable wheel")
        import_path = wheel
    else:
        raise ValueError(f"unknown arm: {arm}")
    elapsed_ns = time.perf_counter_ns() - started
    return {
        "elapsed_ns": elapsed_ns,
        "materialized_runtime_bytes": tree_bytes(target),
        "shared_artifact_bytes": wheel.stat().st_size,
        "artifact_sha256": digest,
        "import_path": str(import_path),
    }


def run_workload(repo: Path, import_path: Path) -> dict[str, Any]:
    env = dict(os.environ)
    # Keep the harness itself bytecode-clean while allowing the projected
    # runtime to exhibit normal Python cache behavior.
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env["PYTHONPATH"] = str(import_path)
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
    before = tree_bytes(target)
    started = time.perf_counter_ns()
    shutil.rmtree(target)
    elapsed_ns = time.perf_counter_ns() - started
    return {
        "elapsed_ns": elapsed_ns,
        "bytes_before": before,
        "bytes_after": tree_bytes(target),
        "target_exists_after": target.exists(),
    }


def summarize(trials: list[dict[str, Any]], wheel_build: dict[str, Any]) -> dict[str, Any]:
    if not trials:
        raise ValueError("no trials")
    semantic = {r["workload"]["payload"]["semantic_sha256"] for r in trials}
    out: dict[str, Any] = {}
    for arm in ARMS:
        rows = [r for r in trials if r["arm"] == arm]
        if not rows:
            continue
        reconstruct_ms = [r["reconstruct"]["elapsed_ns"] / 1e6 for r in rows]
        workload_ms = [r["workload"]["elapsed_ns"] / 1e6 for r in rows]
        discard_ms = [r["discard"]["elapsed_ns"] / 1e6 for r in rows]
        materialized = [r["reconstruct"]["materialized_runtime_bytes"] for r in rows]
        growth = [
            r["discard"]["bytes_before"] - r["reconstruct"]["materialized_runtime_bytes"]
            for r in rows
        ]
        out[arm] = {
            "n": len(rows),
            "median_reconstruct_ms": float(statistics.median(reconstruct_ms)),
            "min_reconstruct_ms": float(min(reconstruct_ms)),
            "max_reconstruct_ms": float(max(reconstruct_ms)),
            "median_materialized_runtime_bytes": float(statistics.median(materialized)),
            "median_post_workload_growth_bytes": float(statistics.median(growth)),
            "median_workload_ms": float(statistics.median(workload_ms)),
            "median_workload_ru_maxrss_kib": float(
                statistics.median(r["workload"]["payload"]["ru_maxrss_kib"] for r in rows)
            ),
            "median_discard_ms": float(statistics.median(discard_ms)),
            "residual_bytes_max": max(r["discard"]["bytes_after"] for r in rows),
            "semantic_hashes": sorted(
                {r["workload"]["payload"]["semantic_sha256"] for r in rows}
            ),
        }
    extract = out.get("wheel_extract", {}).get("median_reconstruct_ms")
    zipimport = out.get("wheel_zipimport", {}).get("median_reconstruct_ms")
    if extract and zipimport:
        out["wheel_zipimport"]["speedup_vs_wheel_extract"] = extract / zipimport
    return {
        "experiment_id": "FRL-REINSTALL-002-ZIPIMPORT-v1",
        "trial_count": len(trials),
        "semantic_parity": len(semantic) == 1,
        "semantic_hashes": sorted(semantic),
        "all_discarded_cleanly": all(
            r["discard"]["bytes_after"] == 0 and not r["discard"]["target_exists_after"]
            for r in trials
        ),
        "canonical_build_residue_delta_bytes": wheel_build[
            "canonical_residue_delta_bytes"
        ],
        "arms": out,
    }


def run_experiment(repo: Path, out_dir: Path, *, blocks: int, seed: int) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = out_dir / "artifacts"
    runtime = out_dir / "runtime"
    wheel, wheel_build = build_wheel_isolated(repo, artifacts)
    expected_sha256 = sha256_file(wheel)
    trials: list[dict[str, Any]] = []
    jsonl = out_dir / "trials.jsonl"
    for block, order, arm in schedule(blocks, seed):
        target = runtime / f"b{block:03d}-o{order}-{arm}"
        rec = reconstruct(
            arm,
            wheel=wheel,
            expected_sha256=expected_sha256,
            target=target,
        )
        workload = run_workload(repo, Path(rec["import_path"]))
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
    summary = summarize(trials, wheel_build)
    summary["blocks"] = blocks
    summary["seed"] = seed
    summary["wheel"] = {
        "name": wheel.name,
        "bytes": wheel.stat().st_size,
        "sha256": expected_sha256,
        "isolated_build_elapsed_ms": wheel_build["elapsed_ns"] / 1e6,
        "isolated_build_peak_rss_kib": wheel_build["peak_rss_kib"],
        "canonical_residue_delta_bytes": wheel_build["canonical_residue_delta_bytes"],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="FRL direct-wheel projection experiment")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--blocks", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20261012)
    args = parser.parse_args()
    result = run_experiment(
        Path(args.repo).resolve(),
        Path(args.out).resolve(),
        blocks=args.blocks,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
