from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

from .app_surface import NoEligibleConfiguration, select_from_policy_path, write_receipt
from .recorder import ingest_many
from .evidence_residency import (
    parse_storage_ref,
    verify_manifest,
    write_manifest,
)


def _dump(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def cmd_catalog(args: argparse.Namespace) -> None:
    from .calculators import CATALOG

    if args.json:
        _dump(CATALOG)
        return
    for name, meta in CATALOG.items():
        print(f"{name:14} {meta['purpose']}")


def cmd_template(args: argparse.Namespace) -> None:
    from .calculators import CATALOG, template

    if args.tool not in CATALOG:
        raise SystemExit(f"unknown calculator: {args.tool}")
    _dump(template(args.tool))


def cmd_run_spec(args: argparse.Namespace) -> None:
    from .calculators import run_spec

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


def cmd_evidence_manifest(args: argparse.Namespace) -> None:
    storage_refs = [
        parse_storage_ref(value)
        for value in args.storage_ref
    ]
    origin = None
    if args.origin_provider or args.origin_ref or args.origin_digest:
        if not args.origin_provider or not args.origin_ref:
            raise SystemExit(
                "--origin-provider and --origin-ref must be supplied together"
            )
        origin = {
            "provider": args.origin_provider,
            "reference": args.origin_ref,
        }
        if args.origin_digest:
            origin["digest"] = args.origin_digest

    manifest = write_manifest(
        args.root,
        args.out,
        experiment_id=args.experiment_id,
        run_id=args.run_id,
        source_commit=args.source_commit,
        residency_tier=args.tier,
        storage_refs=storage_refs,
        origin=origin,
    )
    _dump(
        {
            "status": "PASS",
            "out": str(Path(args.out)),
            "content_set_sha256": manifest["content_set_sha256"],
            "file_count": manifest["file_count"],
            "total_bytes": manifest["total_bytes"],
            "residency_tier": manifest["residency_tier"],
        }
    )


def cmd_evidence_verify(args: argparse.Namespace) -> None:
    result = verify_manifest(
        args.root,
        args.manifest,
        allow_extra=args.allow_extra,
    )
    _dump(result)
    if result["status"] != "PASS":
        raise SystemExit(2)


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def cmd_governor_select(args: argparse.Namespace) -> None:
    try:
        receipt = select_from_policy_path(
            args.policy,
            peak_budget_bytes=args.peak_budget_bytes,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )
    except NoEligibleConfiguration as exc:
        _dump({
            "status": "NO_ELIGIBLE_CONFIGURATION",
            "error": str(exc),
            "peak_budget_bytes": args.peak_budget_bytes,
            "minimum_rank_coverage": args.minimum_rank_coverage,
        })
        raise SystemExit(2)
    write_receipt(receipt, args.out)
    _dump(receipt)


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
    p.add_argument("tool")
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
        "evidence-manifest",
        help="Create a content-addressed HOT/WARM/COLD evidence manifest",
    )
    p.add_argument("root")
    p.add_argument("--out", required=True)
    p.add_argument("--experiment-id", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--source-commit", required=True)
    p.add_argument(
        "--tier",
        required=True,
        choices=["HOT", "WARM", "COLD"],
    )
    p.add_argument(
        "--storage-ref",
        action="append",
        default=[],
        metavar="TIER:PROVIDER:LOCATOR",
        help="Repeatable opaque storage reference; avoid public absolute paths or private URLs",
    )
    p.add_argument("--origin-provider")
    p.add_argument("--origin-ref")
    p.add_argument("--origin-digest")
    p.set_defaults(func=cmd_evidence_manifest)

    p = sub.add_parser(
        "evidence-verify",
        help="Verify a restored evidence directory against a residency manifest",
    )
    p.add_argument("root")
    p.add_argument("--manifest", required=True)
    p.add_argument(
        "--allow-extra",
        action="store_true",
        help="Allow unmanifested files while still verifying all manifested files",
    )
    p.set_defaults(func=cmd_evidence_verify)

    p = sub.add_parser(
        "governor-select",
        help="Select a repaired q from a frozen Governor policy and write an evidence receipt",
    )
    p.add_argument("--policy", required=True)
    p.add_argument("--peak-budget-bytes", type=int, required=True)
    p.add_argument("--minimum-rank-coverage", type=float, default=0.95)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_governor_select)

    p = sub.add_parser(
        "doctor",
        help="Check calculation dependencies",
    )
    p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
