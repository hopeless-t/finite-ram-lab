from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

from .calculators import CATALOG, run_spec, template
from .recorder import ingest_many


def _dump(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def cmd_catalog(args: argparse.Namespace) -> None:
    if args.json:
        _dump(CATALOG)
        return
    for name, meta in CATALOG.items():
        print(f"{name:14} {meta['purpose']}")


def cmd_template(args: argparse.Namespace) -> None:
    _dump(template(args.tool))


def cmd_run_spec(args: argparse.Namespace) -> None:
    result = run_spec(args.spec)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    _dump(
        {
            "status": "PASS",
            "tool": result["tool"],
            "out": str(out),
        }
    )


def cmd_ingest_evidence(args: argparse.Namespace) -> None:
    _dump(
        ingest_many(
            args.inputs,
            args.db,
            rebuild=args.rebuild,
        )
    )


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def cmd_doctor(args: argparse.Namespace) -> None:
    data = {
        "python": platform.python_version(),
        "numpy": _version("numpy"),
        "scipy": _version("scipy"),
        "pandas": _version("pandas"),
    }
    data["analysis_ready"] = all(
        data[name] is not None
        for name in ("numpy", "scipy", "pandas")
    )
    _dump(data)
    if not data["analysis_ready"]:
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="frl",
        description="Finite RAM Lab research calculation toolbox",
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    p = sub.add_parser(
        "catalog",
        help="List ready-made research calculators",
    )
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_catalog)

    p = sub.add_parser(
        "template",
        help="Print a spec template for a calculator",
    )
    p.add_argument(
        "tool",
        choices=sorted(CATALOG),
    )
    p.set_defaults(func=cmd_template)

    p = sub.add_parser(
        "run-spec",
        help="Run one calculation spec",
    )
    p.add_argument("spec")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_run_spec)

    p = sub.add_parser(
        "ingest-evidence",
        help="Build or extend the REC-001 SQLite projection from JSONL evidence",
    )
    p.add_argument("inputs", nargs="+")
    p.add_argument("--db", required=True)
    p.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the existing SQLite projection before ingesting inputs",
    )
    p.set_defaults(func=cmd_ingest_evidence)

    p = sub.add_parser(
        "doctor",
        help="Check calculation dependencies",
    )
    p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
