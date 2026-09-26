from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import subprocess
import time
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot, _touch
from .region_workload import PAGE_SIZE, _mapping, residency


def marker_digest(mm: mmap.mmap, size: int) -> str:
    h = hashlib.sha256()
    for i in range(0, size, PAGE_SIZE):
        h.update(bytes([mm[i]]))
    return h.hexdigest()


def retouch(mm: mmap.mmap, size: int) -> int:
    start = time.perf_counter_ns()
    for i in range(0, size, PAGE_SIZE):
        value = mm[i]
        mm[i] = value
    return time.perf_counter_ns() - start


def request_reclaim(cgroup: Path, reclaim_mib: int) -> dict[str, Any]:
    payload = f"{reclaim_mib}M swappiness=max\n"
    start = time.perf_counter_ns()
    proc = subprocess.run(
        ["sudo", "tee", str(cgroup / "memory.reclaim")],
        input=payload,
        text=True,
        capture_output=True,
    )
    duration = time.perf_counter_ns() - start
    return {
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "payload": payload.strip(),
        "duration_ns": duration,
    }


def run(
    arm: str,
    region_mib: int,
    pageout_mib: int,
    reclaim_mib: int,
) -> dict[str, Any]:
    if arm not in {"pageout_only", "pageout_plus_reclaim"}:
        raise ValueError("invalid arm")
    if pageout_mib > region_mib:
        raise ValueError("pageout_mib must not exceed region_mib")

    region_size = region_mib * 1024 * 1024
    pageout_size = pageout_mib * 1024 * 1024

    target = _mapping(region_size)
    control = _mapping(region_size)
    _touch(target)
    _touch(control)

    rel = _self_cgroup_path()
    cgroup = Path("/sys/fs/cgroup") / rel.lstrip("/")

    digest_target_before = marker_digest(target, region_size)
    digest_control_before = marker_digest(control, region_size)

    before = {
        "target": residency(target, region_size),
        "control": residency(control, region_size),
        "os": _snapshot(cgroup),
    }

    advice = getattr(mmap, "MADV_PAGEOUT", 21)
    pageout_error = None
    pageout_ok = False
    pageout_ns = None
    try:
        start = time.perf_counter_ns()
        target.madvise(advice, 0, pageout_size)
        pageout_ns = time.perf_counter_ns() - start
        pageout_ok = True
    except Exception as exc:
        pageout_error = f"{type(exc).__name__}: {exc}"

    time.sleep(0.10)
    after_pageout = {
        "target": residency(target, region_size),
        "control": residency(control, region_size),
        "os": _snapshot(cgroup),
    }

    reclaim = {
        "attempted": arm == "pageout_plus_reclaim",
        "success": None,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "payload": None,
        "duration_ns": None,
    }
    if arm == "pageout_plus_reclaim":
        reclaim.update(request_reclaim(cgroup, reclaim_mib))
        time.sleep(0.10)

    after_reclaim = {
        "target": residency(target, region_size),
        "control": residency(control, region_size),
        "os": _snapshot(cgroup),
    }

    target_retouch_ns = retouch(target, region_size)
    control_retouch_ns = retouch(control, region_size)

    digest_target_after = marker_digest(target, region_size)
    digest_control_after = marker_digest(control, region_size)
    final_os = _snapshot(cgroup)

    target_drop = (
        before["target"]["resident_fraction"]
        - after_reclaim["target"]["resident_fraction"]
    )
    control_drop = (
        before["control"]["resident_fraction"]
        - after_reclaim["control"]["resident_fraction"]
    )

    events = final_os["memory_events"]
    checks = {
        "pageout_success": pageout_ok,
        "reclaim_success_when_requested": (
            arm == "pageout_only" or bool(reclaim["success"])
        ),
        "target_content_match": digest_target_before == digest_target_after,
        "control_content_match": digest_control_before == digest_control_after,
        "no_oom": (
            events.get("oom", 0) == 0
            and events.get("oom_kill", 0) == 0
        ),
    }

    result = {
        "experiment_id": "ENV-004",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "arm": arm,
        "cgroup_path": rel,
        "parameters": {
            "region_mib": region_mib,
            "pageout_mib": pageout_mib,
            "reclaim_mib": reclaim_mib,
        },
        "pageout": {
            "success": pageout_ok,
            "error": pageout_error,
            "duration_ns": pageout_ns,
        },
        "reclaim": reclaim,
        "before": before,
        "after_pageout": after_pageout,
        "after_reclaim": after_reclaim,
        "retouch": {
            "target_ns": target_retouch_ns,
            "control_ns": control_retouch_ns,
        },
        "derived": {
            "target_residency_drop": target_drop,
            "control_residency_drop": control_drop,
            "target_minus_control_drop": target_drop - control_drop,
            "swap_growth_after_pageout_bytes": (
                after_pageout["os"]["memory_swap_current"]
                - before["os"]["memory_swap_current"]
            ),
            "swap_growth_after_reclaim_bytes": (
                after_reclaim["os"]["memory_swap_current"]
                - before["os"]["memory_swap_current"]
            ),
        },
        "checks": checks,
    }

    target.close()
    control.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=("pageout_only", "pageout_plus_reclaim"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--pageout-mib", type=int, required=True)
    p.add_argument("--reclaim-mib", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.arm,
        args.region_mib,
        args.pageout_mib,
        args.reclaim_mib,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "reclaim": result["reclaim"],
        "derived": result["derived"],
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
