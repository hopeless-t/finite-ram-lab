from __future__ import annotations

import argparse
import json
from pathlib import Path



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
    from .recorder import ingest_many

    _dump(
        ingest_many(
            args.inputs,
            args.db,
            rebuild=args.rebuild,
        )
    )


def cmd_evidence_manifest(args: argparse.Namespace) -> None:
    from .evidence_residency import parse_storage_ref, write_manifest

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
    from .evidence_residency import verify_manifest

    result = verify_manifest(
        args.root,
        args.manifest,
        allow_extra=args.allow_extra,
    )
    _dump(result)
    if result["status"] != "PASS":
        raise SystemExit(2)



CACHE_TRACE_FAMILIES = ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty")


def _trace_from_args(args: argparse.Namespace) -> list[object]:
    from .cache_ops import load_trace_json, synthetic_trace

    if getattr(args, "trace_json", None):
        return load_trace_json(args.trace_json)
    return synthetic_trace(
        family=args.family,
        seed=args.seed,
        length=args.length,
        universe=args.universe,
        capacity_anchor=args.capacity_anchor,
    )


def cmd_cache_doctor(args: argparse.Namespace) -> None:
    from .cache_ops import operational_status

    _dump(operational_status())


def cmd_cache_analyze(args: argparse.Namespace) -> None:
    from .cache_ops import analyze_trace, parse_capacities, trace_digest

    trace = _trace_from_args(args)
    result = analyze_trace(
        trace,
        capacities=parse_capacities(args.capacities),
        fault_rates=args.fault_rate,
        backend=args.backend,
        workers=args.workers,
    )
    result["trace_sha256"] = trace_digest(trace)
    result["trace_source"] = "json" if args.trace_json else "synthetic"
    _dump(result)


def cmd_cache_benchmark(args: argparse.Namespace) -> None:
    from .cache_ops import benchmark_trace, parse_capacities, trace_digest

    trace = _trace_from_args(args)
    result = benchmark_trace(
        trace,
        capacities=parse_capacities(args.capacities),
        anchor_capacity=args.anchor_capacity,
        repeats=args.repeats,
        backend=args.backend,
        workers=args.workers,
    )
    result["trace_sha256"] = trace_digest(trace)
    result["trace_source"] = "json" if args.trace_json else "synthetic"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _dump(result)


def _add_cache_trace_args(p: argparse.ArgumentParser) -> None:
    source = p.add_mutually_exclusive_group()
    source.add_argument("--trace-json", help="JSON array containing a trace; synthetic trace is the default")
    source.add_argument("--family", choices=CACHE_TRACE_FAMILIES, default="shifting_hotset")
    p.add_argument("--seed", type=int, default=20261012)
    p.add_argument("--length", type=int, default=12000)
    p.add_argument("--universe", type=int, default=257)
    p.add_argument("--capacity-anchor", type=int, default=41)
    p.add_argument("--capacities", default="17,41,83,127")
    p.add_argument("--backend", choices=["auto", "native", "python"], default="auto")
    p.add_argument("--workers", default="auto", help="auto or positive integer")


def _normalize_cache_args(args: argparse.Namespace) -> None:
    if hasattr(args, "workers") and args.workers != "auto":
        args.workers = int(args.workers)
        if args.workers <= 0:
            raise SystemExit("--workers must be auto or a positive integer")


def cmd_runtime_status(args: argparse.Namespace) -> None:
    from .operational_runtime import runtime_status

    _dump(runtime_status())


def cmd_runtime_activate(args: argparse.Namespace) -> None:
    from .operational_runtime import activate_wheel

    _dump(activate_wheel(args.wheel, smoke=not args.no_smoke, hot_projection=not args.raw_wheel))


def cmd_runtime_rollback(args: argparse.Namespace) -> None:
    from .operational_runtime import rollback_runtime

    _dump(rollback_runtime())


def cmd_runtime_prune(args: argparse.Namespace) -> None:
    from .operational_runtime import prune_runtime

    _dump(prune_runtime(apply=args.apply))


def cmd_runtime_benchmark(args: argparse.Namespace) -> None:
    from .operational_runtime import benchmark_runtime

    result = benchmark_runtime(
        wheel=args.wheel,
        loops=args.loops,
        process_repeats=args.process_repeats,
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _dump(result)

def _version(name: str) -> str | None:
    import importlib.metadata

    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def cmd_doctor(args: argparse.Namespace) -> None:
    import platform

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
        "cache-doctor",
        help="Show adaptive cache engine capabilities and native backend state",
    )
    p.set_defaults(func=cmd_cache_doctor)

    p = sub.add_parser(
        "cache-analyze",
        help="Analyze one trace with the adaptive LRU/OPT engine",
    )
    _add_cache_trace_args(p)
    p.add_argument(
        "--fault-rate",
        action="append",
        type=float,
        default=[0.10, 0.05],
        help="Repeatable target fault rate for minimum-capacity inversion",
    )
    p.set_defaults(func=cmd_cache_analyze)

    p = sub.add_parser(
        "cache-benchmark",
        help="Benchmark scalar reference versus installed adaptive cache engine",
    )
    _add_cache_trace_args(p)
    p.add_argument("--anchor-capacity", type=int, default=41)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--out")
    p.set_defaults(func=cmd_cache_benchmark)

    p = sub.add_parser(
        "runtime-status",
        help="Show the active content-addressed wheel runtime",
    )
    p.set_defaults(func=cmd_runtime_status)

    p = sub.add_parser(
        "runtime-activate",
        help="Smoke-test and atomically activate a candidate wheel",
    )
    p.add_argument("wheel")
    p.add_argument("--no-smoke", action="store_true")
    p.add_argument("--raw-wheel", action="store_true", help="Activate the source wheel without hot-pyc projection")
    p.set_defaults(func=cmd_runtime_activate)

    p = sub.add_parser(
        "runtime-rollback",
        help="Smoke-test and atomically roll back to the previous wheel",
    )
    p.set_defaults(func=cmd_runtime_rollback)

    p = sub.add_parser(
        "runtime-prune",
        help="Remove runtime artifacts unreachable from current/previous",
    )
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_runtime_prune)

    p = sub.add_parser(
        "runtime-benchmark",
        help="Benchmark the active operational runtime and reinstall path",
    )
    p.add_argument("--wheel")
    p.add_argument("--loops", type=int, default=20)
    p.add_argument("--process-repeats", type=int, default=10)
    p.add_argument("--out")
    p.set_defaults(func=cmd_runtime_benchmark)

    p = sub.add_parser(
        "doctor",
        help="Check calculation dependencies",
    )
    p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    _normalize_cache_args(args)
    args.func(args)


if __name__ == "__main__":
    main()
