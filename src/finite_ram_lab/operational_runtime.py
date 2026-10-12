from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .wheel_projection import PROJECTION_ID, project_hot_pyc_wheel

SMOKE_CONTRACT = "cache-doctor+cache-analyze+runtime-status-v2"


def default_root() -> Path:
    raw = os.environ.get("FRL_RUNTIME_ROOT")
    return Path(raw).expanduser() if raw else Path.home() / ".local" / "share" / "finite-ram-lab"


def default_launcher() -> Path:
    raw = os.environ.get("FRL_LAUNCHER")
    return Path(raw).expanduser() if raw else Path.home() / ".local" / "bin" / "frl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _identity(path: Path) -> list[int]:
    st = path.stat()
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def _epoch_path(path: Path, epochs: Path) -> Path:
    key = hashlib.sha256(str(path.resolve(strict=False)).encode()).hexdigest()
    return epochs / f"{key}.json"


def _record_epoch(path: Path, digest: str, epochs: Path) -> None:
    epochs.mkdir(parents=True, exist_ok=True)
    target = _epoch_path(path, epochs)
    data = {"path": str(path.resolve(strict=False)), "identity": _identity(path), "sha256": digest}
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def _digest_with_epoch(path: Path, epochs: Path) -> tuple[str, bool]:
    epoch = _epoch_path(path, epochs)
    if epoch.exists():
        try:
            data = json.loads(epoch.read_text(encoding="utf-8"))
            if data.get("path") == str(path.resolve(strict=False)) and data.get("identity") == _identity(path):
                return str(data["sha256"]), True
        except (OSError, KeyError, json.JSONDecodeError):
            pass
    digest = sha256_file(path)
    _record_epoch(path, digest, epochs)
    return digest, False


def _python_fingerprint(python: str) -> str:
    requested = Path(python).resolve(strict=False)
    current = Path(sys.executable).resolve(strict=False)
    if requested == current:
        payload = "|".join(
            [
                str(current),
                sys.version,
                platform.system(),
                platform.machine(),
                ":".join(platform.libc_ver()),
            ]
        )
    else:
        proc = subprocess.run(
            [python, "-c", "import json,platform,sys;print(json.dumps([sys.executable,sys.version,platform.system(),platform.machine(),platform.libc_ver()]))"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        payload = proc.stdout.strip()
    return hashlib.sha256(payload.encode()).hexdigest()


def _atomic_symlink(target: Path, link: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_name(f".{link.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    relative = os.path.relpath(target, link.parent)
    os.symlink(relative, tmp)
    os.replace(tmp, link)


def _launcher_text(root: Path, python: str) -> str:
    current = root / "current.whl"
    control = root / "control.whl"
    return f'''#!/bin/sh
set -eu
case "${{1:-}}" in
  runtime-*) FRL_WHEEL="{control}" ;;
  *)         FRL_WHEEL="{current}" ;;
esac
if [ ! -e "$FRL_WHEEL" ]; then
  echo "frl: runtime artifact missing: $FRL_WHEEL" >&2
  exit 70
fi
exec env PYTHONPATH="$FRL_WHEEL${{PYTHONPATH:+:$PYTHONPATH}}" "{python}" -m finite_ram_lab "$@"
'''


def _write_launcher(path: Path, *, root: Path, python: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _launcher_text(root, python)
    if path.exists() and path.read_text(encoding="utf-8") == text and (path.stat().st_mode & 0o111):
        return False
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o755)
    os.replace(tmp, path)
    return True


def _smoke(artifact: Path, *, python: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(artifact)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    commands = [
        [python, "-m", "finite_ram_lab", "cache-doctor"],
        [
            python,
            "-m",
            "finite_ram_lab",
            "cache-analyze",
            "--length",
            "300",
            "--universe",
            "29",
            "--capacity-anchor",
            "7",
            "--capacities",
            "3,7,17",
        ],
        [python, "-m", "finite_ram_lab", "runtime-status"],
    ]
    rows = []
    for argv in commands:
        t0 = time.perf_counter_ns()
        proc = subprocess.run(
            argv,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
        rows.append(
            {
                "argv": argv[2:],
                "returncode": proc.returncode,
                "elapsed_ms": elapsed_ms,
                "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                "stderr_tail": proc.stderr[-1000:],
            }
        )
        if proc.returncode != 0:
            raise RuntimeError(f"candidate smoke failed: {argv}: {proc.stderr[-1000:]}")
    return {"status": "PASS", "reused": False, "commands": rows}


def _store_source(source: Path, sources: Path, digest: str, epochs: Path) -> tuple[Path, bool, float]:
    stored = sources / f"{digest}.whl"
    sources.mkdir(parents=True, exist_ok=True)
    if stored.exists():
        stored_digest, _reused = _digest_with_epoch(stored, epochs)
        if stored_digest == digest:
            return stored, False, 0.0
    t0 = time.perf_counter_ns()
    tmp = sources / f".{digest}.{os.getpid()}.tmp"
    shutil.copy2(source, tmp)
    if sha256_file(tmp) != digest:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("source wheel digest changed during copy")
    os.replace(tmp, stored)
    _record_epoch(stored, digest, epochs)
    return stored, True, (time.perf_counter_ns() - t0) / 1e6


def _project_artifact(
    source: Path,
    source_digest: str,
    *,
    root: Path,
    hot_projection: bool,
    epochs: Path,
) -> tuple[Path, str, dict[str, Any], bool, float, bool]:
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    if not hot_projection:
        artifact = artifacts / f"{source_digest}.whl"
        epoch_reused = False
        if artifact.exists():
            artifact_digest, epoch_reused = _digest_with_epoch(artifact, epochs)
            if artifact_digest == source_digest:
                return artifact, source_digest, {"projection_id": "raw-wheel"}, False, 0.0, epoch_reused
        tmp = artifacts / f".{source_digest}.{os.getpid()}.tmp"
        shutil.copy2(source, tmp)
        os.replace(tmp, artifact)
        _record_epoch(artifact, source_digest, epochs)
        return artifact, source_digest, {"projection_id": "raw-wheel"}, False, 0.0, False

    projections = root / "projections"
    projections.mkdir(parents=True, exist_ok=True)
    key = f"{source_digest}-{sys.implementation.cache_tag}-{PROJECTION_ID}"
    index_path = projections / f"{key}.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            digest = index["artifact_sha256"]
            artifact = artifacts / f"{digest}.whl"
            if artifact.exists():
                artifact_digest, epoch_reused = _digest_with_epoch(artifact, epochs)
                if artifact_digest == digest:
                    return artifact, digest, index["projection"], False, 0.0, epoch_reused
        except (KeyError, json.JSONDecodeError, OSError):
            pass

    t0 = time.perf_counter_ns()
    temp_projection = projections / f".{key}.{os.getpid()}.tmp.whl"
    projection = project_hot_pyc_wheel(source, temp_projection)
    digest = str(projection["sha256"])
    artifact = artifacts / f"{digest}.whl"
    if artifact.exists():
        existing_digest, _ = _digest_with_epoch(artifact, epochs)
        if existing_digest == digest:
            temp_projection.unlink(missing_ok=True)
        else:
            os.replace(temp_projection, artifact)
    else:
        os.replace(temp_projection, artifact)
    _record_epoch(artifact, digest, epochs)
    index = {
        "source_sha256": source_digest,
        "artifact_sha256": digest,
        "projection": projection,
    }
    tmp_index = index_path.with_name(f".{index_path.name}.{os.getpid()}.tmp")
    tmp_index.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_index, index_path)
    return artifact, digest, projection, True, (time.perf_counter_ns() - t0) / 1e6, False


def activate_wheel(
    wheel: str | Path,
    *,
    root: str | Path | None = None,
    launcher: str | Path | None = None,
    python: str | None = None,
    smoke: bool = True,
    hot_projection: bool = True,
) -> dict[str, Any]:
    source = Path(wheel).resolve()
    if not source.is_file() or source.suffix != ".whl":
        raise ValueError("wheel must be an existing .whl file")
    root_path = Path(root).expanduser() if root is not None else default_root()
    launcher_path = Path(launcher).expanduser() if launcher is not None else default_launcher()
    python_exe = python or sys.executable
    sources = root_path / "sources"
    manifests = root_path / "manifests"
    epochs = root_path / "epochs"
    manifests.mkdir(parents=True, exist_ok=True)

    total0 = time.perf_counter_ns()
    source_digest, source_epoch_reused = _digest_with_epoch(source, epochs)
    stored_source, source_copied, copy_ms = _store_source(source, sources, source_digest, epochs)
    artifact, digest, projection, projected, projection_ms, artifact_epoch_reused = _project_artifact(
        stored_source,
        source_digest,
        root=root_path,
        hot_projection=hot_projection,
        epochs=epochs,
    )

    manifest_path = manifests / f"{digest}.json"
    python_fingerprint = _python_fingerprint(python_exe)
    cached_manifest: dict[str, Any] | None = None
    if manifest_path.exists():
        try:
            cached_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cached_manifest = None

    smoke_reused = False
    if smoke:
        if (
            cached_manifest
            and cached_manifest.get("sha256") == digest
            and cached_manifest.get("python_fingerprint") == python_fingerprint
            and cached_manifest.get("smoke_contract") == SMOKE_CONTRACT
            and cached_manifest.get("smoke", {}).get("status") == "PASS"
        ):
            smoke_result = dict(cached_manifest["smoke"])
            smoke_result["reused"] = True
            smoke_reused = True
        else:
            smoke_result = _smoke(artifact, python=python_exe)
    else:
        smoke_result = {"status": "SKIP", "reused": False, "commands": []}

    current = root_path / "current.whl"
    previous = root_path / "previous.whl"
    control = root_path / "control.whl"
    old_target: Path | None = None
    if current.is_symlink():
        old_target = current.resolve(strict=False)
    elif current.exists():
        raise RuntimeError("current.whl exists but is not a symlink")

    t_switch = time.perf_counter_ns()
    switched = False
    if old_target is not None and old_target != artifact:
        _atomic_symlink(old_target, previous)
    if old_target != artifact:
        _atomic_symlink(artifact, current)
        switched = True
    control_target = control.resolve(strict=False) if control.is_symlink() else None
    control_switched = control_target != artifact
    if control_switched:
        _atomic_symlink(artifact, control)
    launcher_written = _write_launcher(launcher_path, root=root_path, python=python_exe)
    switch_ms = (time.perf_counter_ns() - t_switch) / 1e6

    manifest = {
        "sha256": digest,
        "source_sha256": source_digest,
        "artifact": str(artifact),
        "bytes": artifact.stat().st_size,
        "python": python_exe,
        "python_fingerprint": python_fingerprint,
        "smoke_contract": SMOKE_CONTRACT,
        "projection": projection,
        "smoke": smoke_result if smoke_result.get("status") != "SKIP" else (cached_manifest or {}).get("smoke", smoke_result),
    }
    if cached_manifest != manifest:
        tmp_manifest = manifest_path.with_name(f".{manifest_path.name}.{os.getpid()}.tmp")
        tmp_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp_manifest, manifest_path)

    return {
        "status": "PASS",
        "source_sha256": source_digest,
        "sha256": digest,
        "artifact": str(artifact),
        "artifact_bytes": artifact.stat().st_size,
        "source_copied": source_copied,
        "source_epoch_reused": source_epoch_reused,
        "artifact_epoch_reused": artifact_epoch_reused,
        "copy_ms": copy_ms,
        "projected": projected,
        "projection_ms": projection_ms,
        "projection": projection,
        "smoke_reused": smoke_reused,
        "switch_ms": switch_ms,
        "switched": switched,
        "control_switched": control_switched,
        "launcher_written": launcher_written,
        "total_ms": (time.perf_counter_ns() - total0) / 1e6,
        "current": str(current),
        "previous": str(previous) if previous.exists() or previous.is_symlink() else None,
        "launcher": str(launcher_path),
        "launcher_bytes": launcher_path.stat().st_size,
        "smoke": smoke_result,
    }


def runtime_status(*, root: str | Path | None = None, launcher: str | Path | None = None) -> dict[str, Any]:
    root_path = Path(root).expanduser() if root is not None else default_root()
    launcher_path = Path(launcher).expanduser() if launcher is not None else default_launcher()
    artifacts = root_path / "artifacts"
    sources = root_path / "sources"
    current = root_path / "current.whl"
    previous = root_path / "previous.whl"
    control = root_path / "control.whl"

    def link_info(link: Path) -> dict[str, Any] | None:
        if not link.is_symlink():
            return None
        target = link.resolve(strict=False)
        return {
            "link": str(link),
            "target": str(target),
            "exists": target.exists(),
            "sha256": sha256_file(target) if target.exists() else None,
            "bytes": target.stat().st_size if target.exists() else None,
        }

    return {
        "root": str(root_path),
        "launcher": str(launcher_path),
        "launcher_exists": launcher_path.exists(),
        "current": link_info(current),
        "previous": link_info(previous),
        "control": link_info(control),
        "artifact_count": len(list(artifacts.glob("*.whl"))) if artifacts.exists() else 0,
        "artifact_bytes": sum(p.stat().st_size for p in artifacts.glob("*.whl")) if artifacts.exists() else 0,
        "source_count": len(list(sources.glob("*.whl"))) if sources.exists() else 0,
        "source_bytes": sum(p.stat().st_size for p in sources.glob("*.whl")) if sources.exists() else 0,
    }


def prune_runtime(*, root: str | Path | None = None, apply: bool = False) -> dict[str, Any]:
    root_path = Path(root).expanduser() if root is not None else default_root()
    artifacts = root_path / "artifacts"
    sources = root_path / "sources"
    manifests = root_path / "manifests"
    projections = root_path / "projections"
    epochs = root_path / "epochs"
    current = root_path / "current.whl"
    previous = root_path / "previous.whl"
    control = root_path / "control.whl"

    keep_artifacts: set[Path] = set()
    for link in (current, previous, control):
        if link.is_symlink():
            try:
                keep_artifacts.add(link.resolve(strict=True))
            except FileNotFoundError:
                pass

    keep_digests = {p.stem for p in keep_artifacts}
    keep_sources: set[str] = set()
    for digest in keep_digests:
        manifest = manifests / f"{digest}.json"
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                source_digest = data.get("source_sha256")
                if source_digest:
                    keep_sources.add(str(source_digest))
            except (OSError, json.JSONDecodeError):
                pass

    candidates: list[Path] = []
    if artifacts.exists():
        candidates += [p for p in artifacts.glob("*.whl") if p not in keep_artifacts]
    if sources.exists():
        candidates += [p for p in sources.glob("*.whl") if p.stem not in keep_sources]
    if manifests.exists():
        candidates += [p for p in manifests.glob("*.json") if p.stem not in keep_digests]
    if projections.exists():
        for p in projections.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("artifact_sha256") not in keep_digests:
                    candidates.append(p)
            except (OSError, json.JSONDecodeError):
                candidates.append(p)
    candidate_paths = {str(p.resolve(strict=False)) for p in candidates}
    if epochs.exists():
        for p in epochs.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                tracked = Path(data.get("path", ""))
                tracked_resolved = str(tracked.resolve(strict=False)) if str(tracked) else ""
                if not tracked.exists() or tracked_resolved in candidate_paths:
                    candidates.append(p)
            except (OSError, json.JSONDecodeError):
                candidates.append(p)

    unique = list(dict.fromkeys(candidates))
    reclaim = sum(p.stat().st_size for p in unique if p.exists())
    removed = []
    if apply:
        for p in unique:
            if p.exists() or p.is_symlink():
                p.unlink()
                removed.append(str(p))
    return {
        "status": "PASS",
        "apply": apply,
        "keep_artifacts": sorted(str(p) for p in keep_artifacts),
        "keep_source_digests": sorted(keep_sources),
        "candidate_count": len(unique),
        "reclaimable_bytes": reclaim,
        "removed": removed,
    }



def _process_bench(argv: list[str], repeats: int) -> dict[str, float]:
    import statistics

    values: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        subprocess.run(
            argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        values.append((time.perf_counter_ns() - t0) / 1e6)
    values.sort()
    return {
        "n": float(repeats),
        "median_ms": float(statistics.median(values)),
        "p95_ms": float(values[max(0, int(repeats * 0.95) - 1)]),
        "min_ms": float(values[0]),
        "max_ms": float(values[-1]),
    }


def _current_source_wheel(root: Path) -> Path:
    current = root / "current.whl"
    if not current.is_symlink():
        raise RuntimeError("no active current.whl runtime")
    artifact = current.resolve(strict=True)
    digest = artifact.stem
    manifest = root / "manifests" / f"{digest}.json"
    if not manifest.exists():
        raise RuntimeError(f"active runtime manifest is missing: {manifest}")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    source_digest = data.get("source_sha256")
    if not source_digest:
        raise RuntimeError("active runtime manifest does not record source_sha256")
    source = root / "sources" / f"{source_digest}.whl"
    if not source.exists():
        raise RuntimeError(f"active runtime source wheel is missing: {source}")
    return source


def benchmark_runtime(
    *,
    wheel: str | Path | None = None,
    loops: int = 20,
    process_repeats: int = 10,
    root: str | Path | None = None,
    launcher: str | Path | None = None,
) -> dict[str, Any]:
    import statistics

    if loops <= 0 or process_repeats <= 0:
        raise ValueError("loops and process_repeats must be positive")
    root_path = Path(root).expanduser() if root is not None else default_root()
    launcher_path = Path(launcher).expanduser() if launcher is not None else default_launcher()
    source = Path(wheel).expanduser().resolve() if wheel is not None else _current_source_wheel(root_path)

    # Establish a warm epoch first. This is outside the timed repeated loop.
    warm = activate_wheel(source, root=root_path, launcher=launcher_path)
    rows: list[dict[str, Any]] = []
    for _ in range(loops):
        result = activate_wheel(source, root=root_path, launcher=launcher_path)
        rows.append(
            {
                key: result[key]
                for key in (
                    "total_ms",
                    "switch_ms",
                    "source_epoch_reused",
                    "artifact_epoch_reused",
                    "smoke_reused",
                    "projected",
                    "switched",
                    "control_switched",
                    "launcher_written",
                )
            }
        )
    totals = sorted(float(row["total_ms"]) for row in rows)
    switches = sorted(float(row["switch_ms"]) for row in rows)

    process = {
        "help": _process_bench([str(launcher_path), "--help"], process_repeats),
        "cache_doctor": _process_bench([str(launcher_path), "cache-doctor"], process_repeats),
        "cache_analyze_standard": _process_bench(
            [
                str(launcher_path),
                "cache-analyze",
                "--length",
                "12000",
                "--universe",
                "257",
                "--capacity-anchor",
                "41",
                "--capacities",
                "17,41,83,127",
            ],
            process_repeats,
        ),
        "runtime_status": _process_bench([str(launcher_path), "runtime-status"], process_repeats),
    }
    return {
        "benchmark": "operational-runtime-v1",
        "source_wheel": str(source),
        "warmup": {
            key: warm[key]
            for key in (
                "total_ms",
                "source_epoch_reused",
                "artifact_epoch_reused",
                "smoke_reused",
                "projected",
                "switched",
                "control_switched",
            )
        },
        "reactivate": {
            "loops": loops,
            "median_ms": float(statistics.median(totals)),
            "p95_ms": float(totals[max(0, int(loops * 0.95) - 1)]),
            "min_ms": totals[0],
            "max_ms": totals[-1],
            "median_switch_ms": float(statistics.median(switches)),
            "all_source_epoch_reused": all(bool(row["source_epoch_reused"]) for row in rows),
            "all_artifact_epoch_reused": all(bool(row["artifact_epoch_reused"]) for row in rows),
            "all_smoke_reused": all(bool(row["smoke_reused"]) for row in rows),
            "any_projected": any(bool(row["projected"]) for row in rows),
            "any_switched": any(bool(row["switched"]) for row in rows),
            "any_control_switched": any(bool(row["control_switched"]) for row in rows),
            "any_launcher_written": any(bool(row["launcher_written"]) for row in rows),
        },
        "process": process,
        "runtime": runtime_status(root=root_path, launcher=launcher_path),
    }



def rollback_runtime(
    *,
    root: str | Path | None = None,
    launcher: str | Path | None = None,
    python: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root).expanduser() if root is not None else default_root()
    launcher_path = Path(launcher).expanduser() if launcher is not None else default_launcher()
    python_exe = python or sys.executable
    current = root_path / "current.whl"
    previous = root_path / "previous.whl"
    manifests = root_path / "manifests"
    epochs = root_path / "epochs"
    if not previous.is_symlink():
        raise RuntimeError("no previous runtime is available")
    previous_target = previous.resolve(strict=True)
    current_target = current.resolve(strict=True) if current.is_symlink() else None
    digest, epoch_reused = _digest_with_epoch(previous_target, epochs)
    fingerprint = _python_fingerprint(python_exe)
    manifest_path = manifests / f"{digest}.json"
    cached = None
    if manifest_path.exists():
        try:
            cached = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cached = None
    smoke_reused = bool(
        cached
        and cached.get("sha256") == digest
        and cached.get("python_fingerprint") == fingerprint
        and cached.get("smoke_contract") == SMOKE_CONTRACT
        and cached.get("smoke", {}).get("status") == "PASS"
    )
    if smoke_reused:
        smoke = dict(cached["smoke"])
        smoke["reused"] = True
    else:
        smoke = _smoke(previous_target, python=python_exe)
        refreshed = dict(cached or {})
        refreshed.update(
            {
                "sha256": digest,
                "artifact": str(previous_target),
                "bytes": previous_target.stat().st_size,
                "python": python_exe,
                "python_fingerprint": fingerprint,
                "smoke_contract": SMOKE_CONTRACT,
                "smoke": smoke,
            }
        )
        manifests.mkdir(parents=True, exist_ok=True)
        tmp_manifest = manifest_path.with_name(f".{manifest_path.name}.{os.getpid()}.tmp")
        tmp_manifest.write_text(json.dumps(refreshed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp_manifest, manifest_path)
    t0 = time.perf_counter_ns()
    if current_target is not None:
        _atomic_symlink(current_target, previous)
    _atomic_symlink(previous_target, current)
    launcher_written = _write_launcher(launcher_path, root=root_path, python=python_exe)
    switch_ms = (time.perf_counter_ns() - t0) / 1e6
    return {
        "status": "PASS",
        "current": str(previous_target),
        "sha256": digest,
        "artifact_epoch_reused": epoch_reused,
        "smoke_reused": smoke_reused,
        "switch_ms": switch_ms,
        "launcher_written": launcher_written,
        "smoke": smoke,
    }
