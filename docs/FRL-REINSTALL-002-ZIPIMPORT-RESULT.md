# FRL-REINSTALL-002 Zipimport Result — 2026-10-12

Status: LOCAL 50-TRIAL PASS

## Question

After a verified immutable wheel exists, is extraction itself necessary for this pure-Python runtime projection?

## Design

Two arms, randomized within 25 blocks:

- `wheel_extract`: SHA-256 verify the canonical wheel, extract it into a fresh runtime directory, then execute.
- `wheel_zipimport`: SHA-256 verify the same canonical wheel and execute directly from the wheel with Python zipimport. No package tree is materialized.

The wheel itself is built from an isolated temporary copy of `pyproject.toml` + `src/`. This prevents setuptools/pip build residue from mutating the canonical repository.

## Evidence

- `evidence/FRL-REINSTALL-002/local-20261012-v1-run1/summary.json`
- `evidence/FRL-REINSTALL-002/local-20261012-v1-run1/trials.jsonl`
- 25 blocks / 50 total trials

All 50 trials produced semantic hash:

`c8bbd8d0eddfea03aa6674b2201be8a6cf060303a8c2b7dab096252442e2cc97`

Canonical build residue delta: **0 bytes**.

## Result

| Metric | wheel_extract | wheel_zipimport |
|---|---:|---:|
| median reconstruct | 18.165 ms | 1.140 ms |
| reconstruct speedup | 1.00x | 15.93x |
| materialized runtime before workload | 1,480,202 B | **0 B** |
| post-workload runtime growth | 6,291 B | **0 B** |
| median workload | 52.541 ms | 52.621 ms |
| median workload max RSS | 24,032 KiB | 24,032 KiB |
| max residual after discard | 0 B | 0 B |

The direct-wheel arm therefore removed extraction and all per-runtime package-tree materialization without changing the tested semantics or measured workload RSS.

## End-to-end correction

The reconstruction-only speedup is large, but the workload dominates the lifecycle.

Median reconstruct + workload:

- `wheel_extract`: 70.705 ms
- `wheel_zipimport`: 53.772 ms

So the observed ready-to-result improvement is **1.315x**, or about **23.95% lower latency**, not 15.93x.

Reconstruction occupied roughly 25.7% of ready-to-result latency in the extraction arm and only 2.1% in the zipimport arm.

This is the more useful systems interpretation: after projection is reduced to ~1 ms, further reinstall optimization has sharply diminishing user-visible returns unless process startup or workload execution is attacked next.

## Where the remaining ~1.14 ms went

A local microbenchmark on the 423,726-byte wheel found:

- full SHA-256: median ~0.948 ms
- `stat`: median ~0.00155 ms
- `zipfile.is_zipfile`: median ~0.0126 ms

Therefore most of the remaining reconstruction cost is integrity verification, not runtime reconstruction.

## Next hypothesis

Move integrity verification from every activation to an **artifact epoch**:

1. hash once when an immutable artifact enters the verified pool;
2. retain the verified digest + filesystem identity tuple;
3. on each activation, perform a cheap identity check;
4. rehash only when identity changes or policy requests a stronger check.

This trades a small amount of trusted control-plane state for lower activation latency. It should be studied explicitly rather than silently weakening integrity semantics.
