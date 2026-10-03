from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

SCHEMA = "finite-ram-lab.meta-qualifier/v0.1"
META_RE = re.compile(r"^src/finite_ram_lab/(fr_meta_[A-Za-z0-9_]+)\.py$")


def discover_modules(paths: Iterable[str]) -> list[str]:
    modules = []
    for raw in paths:
        path = raw.strip()
        match = META_RE.fullmatch(path)
        if match:
            modules.append(match.group(1))
    return sorted(set(modules))


def changed_files(base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def qualify_module(module_name: str) -> dict:
    module = importlib.import_module(f"finite_ram_lab.{module_name}")
    run_panel = getattr(module, "run_panel", None)
    if not callable(run_panel):
        raise RuntimeError(f"meta_module_missing_run_panel:{module_name}")
    result = run_panel()
    if not isinstance(result, dict):
        raise RuntimeError(f"meta_module_non_dict_result:{module_name}")
    if result.get("status") != "PASS":
        raise RuntimeError(f"meta_module_not_pass:{module_name}:{result.get('status')}")
    return result


def qualify_changed(paths: Iterable[str], out_dir: str | Path) -> dict:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    modules = discover_modules(paths)
    receipts = []
    for module_name in modules:
        result = qualify_module(module_name)
        path = root / f"{module_name}.json"
        path.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        receipts.append({"module": module_name, "path": path.name, "status": "PASS"})

    summary = {
        "schema": SCHEMA,
        "status": "PASS",
        "modules": modules,
        "qualified_count": len(receipts),
        "receipts": receipts,
    }
    (root / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from", default="HEAD^")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    paths = changed_files(args.changed_from)
    print(json.dumps(qualify_changed(paths, args.out_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
