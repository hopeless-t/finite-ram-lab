from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FAST_COMMANDS = {
    "cache-doctor",
    "cache-analyze",
    "cache-benchmark",
    "runtime-status",
    "runtime-activate",
    "runtime-rollback",
    "runtime-prune",
    "runtime-benchmark",
}
TRACE_FAMILIES = ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty")


def _dump(data: object) -> None:
    sys.stdout.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _normalize_workers(value: str) -> int | str:
    if value == "auto":
        return value
    workers = int(value)
    if workers <= 0:
        raise SystemExit("--workers must be auto or a positive integer")
    return workers


def _add_trace_args(p: argparse.ArgumentParser) -> None:
    source = p.add_mutually_exclusive_group()
    source.add_argument("--trace-json")
    source.add_argument("--family", choices=TRACE_FAMILIES, default="shifting_hotset")
    p.add_argument("--seed", type=int, default=20261012)
    p.add_argument("--length", type=int, default=12000)
    p.add_argument("--universe", type=int, default=257)
    p.add_argument("--capacity-anchor", type=int, default=41)
    p.add_argument("--capacities", default="17,41,83,127")
    p.add_argument("--backend", choices=["auto", "native", "python"], default="auto")
    p.add_argument("--workers", default="auto")


def _trace(args: argparse.Namespace) -> list[object]:
    from .cache_ops import load_trace_json, synthetic_trace

    if args.trace_json:
        return load_trace_json(args.trace_json)
    return synthetic_trace(
        family=args.family,
        seed=args.seed,
        length=args.length,
        universe=args.universe,
        capacity_anchor=args.capacity_anchor,
    )


def _cache_doctor() -> None:
    from .cache_ops import operational_status

    _dump(operational_status())


def _runtime_status() -> None:
    from .operational_runtime import runtime_status

    _dump(runtime_status())


def _cache_analyze(argv: list[str]) -> None:
    from .cache_ops import analyze_trace, parse_capacities, trace_digest

    p = argparse.ArgumentParser(prog="frl cache-analyze")
    _add_trace_args(p)
    p.add_argument("--fault-rate", action="append", type=float, default=[0.10, 0.05])
    args = p.parse_args(argv)
    trace = _trace(args)
    result = analyze_trace(
        trace,
        capacities=parse_capacities(args.capacities),
        fault_rates=args.fault_rate,
        backend=args.backend,
        workers=_normalize_workers(args.workers),
    )
    result["trace_sha256"] = trace_digest(trace)
    result["trace_source"] = "json" if args.trace_json else "synthetic"
    _dump(result)


def _cache_benchmark(argv: list[str]) -> None:
    from .cache_ops import benchmark_trace, parse_capacities, trace_digest

    p = argparse.ArgumentParser(prog="frl cache-benchmark")
    _add_trace_args(p)
    p.add_argument("--anchor-capacity", type=int, default=41)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--out")
    args = p.parse_args(argv)
    trace = _trace(args)
    result = benchmark_trace(
        trace,
        capacities=parse_capacities(args.capacities),
        anchor_capacity=args.anchor_capacity,
        repeats=args.repeats,
        backend=args.backend,
        workers=_normalize_workers(args.workers),
    )
    result["trace_sha256"] = trace_digest(trace)
    result["trace_source"] = "json" if args.trace_json else "synthetic"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _dump(result)


def _runtime_activate(argv: list[str]) -> None:
    from .operational_runtime import activate_wheel

    p = argparse.ArgumentParser(prog="frl runtime-activate")
    p.add_argument("wheel")
    p.add_argument("--no-smoke", action="store_true")
    p.add_argument("--raw-wheel", action="store_true")
    args = p.parse_args(argv)
    _dump(activate_wheel(args.wheel, smoke=not args.no_smoke, hot_projection=not args.raw_wheel))


def _runtime_benchmark(argv: list[str]) -> None:
    from .operational_runtime import benchmark_runtime

    p = argparse.ArgumentParser(prog="frl runtime-benchmark")
    p.add_argument("--wheel")
    p.add_argument("--loops", type=int, default=20)
    p.add_argument("--process-repeats", type=int, default=10)
    p.add_argument("--out")
    args = p.parse_args(argv)
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


def _runtime_prune(argv: list[str]) -> None:
    from .operational_runtime import prune_runtime

    p = argparse.ArgumentParser(prog="frl runtime-prune")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args(argv)
    _dump(prune_runtime(apply=args.apply))


def _runtime_rollback(argv: list[str]) -> None:
    from .operational_runtime import rollback_runtime

    p = argparse.ArgumentParser(prog="frl runtime-rollback")
    p.parse_args(argv)
    _dump(rollback_runtime())


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise SystemExit("fast CLI requires a subcommand")
    command, rest = args[0], args[1:]
    if command == "cache-doctor":
        if rest:
            raise SystemExit("cache-doctor takes no arguments")
        _cache_doctor()
    elif command == "runtime-status":
        if rest:
            raise SystemExit("runtime-status takes no arguments")
        _runtime_status()
    elif command == "cache-analyze":
        _cache_analyze(rest)
    elif command == "cache-benchmark":
        _cache_benchmark(rest)
    elif command == "runtime-activate":
        _runtime_activate(rest)
    elif command == "runtime-rollback":
        _runtime_rollback(rest)
    elif command == "runtime-prune":
        _runtime_prune(rest)
    elif command == "runtime-benchmark":
        _runtime_benchmark(rest)
    else:
        raise SystemExit(f"unsupported fast command: {command}")
