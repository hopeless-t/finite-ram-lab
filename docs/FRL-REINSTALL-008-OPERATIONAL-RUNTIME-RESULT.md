# FRL-REINSTALL-008 — Operational Runtime / Full-Use Reinstall Loop

Date: 2026-10-12
Status: **GAYA-CENTRAL OPERATIONAL / BOUNDED CONVERGENCE**

## Result in one sentence

Finite RAM Lab's adaptive cache engine is no longer repo-only research code: GAYA-CENTRAL now has an ordinary `frl` command backed by a content-addressed, rollback-capable wheel runtime with built-in analysis and benchmark commands.

## Ordinary user surface

The installed launcher is:

```text
~/.local/bin/frl
```

The operational surface is:

```bash
frl cache-doctor
frl cache-analyze
frl cache-benchmark
frl runtime-status
frl runtime-activate candidate.whl
frl runtime-rollback
frl runtime-prune
frl runtime-benchmark
```

`cache-analyze` accepts either a synthetic trace or a JSON trace. It exposes LRU/OPT comparison, complete LRU capacity curves, and minimum-capacity inversion for target fault rates.

`cache-benchmark` compares the original scalar algorithms with the installed adaptive engine and refuses to report a valid result if LRU/OPT parity fails.

`runtime-benchmark` benchmarks the active reinstall/runtime path without requiring the operator to locate the source wheel manually.

## Why this is not a normal pip install

A conventional install would expand the wheel into `site-packages`, reintroducing the per-runtime materialization that the earlier reinstall experiments had removed.

The operational runtime instead keeps immutable wheels:

```text
~/.local/share/finite-ram-lab/
  sources/<source-sha>.whl       canonical source wheel
  artifacts/<artifact-sha>.whl  runtime projection
  current.whl -> artifact        active app/data plane
  previous.whl -> artifact       one-step rollback
  control.whl -> artifact        latest known-good update/control plane
  manifests/                     smoke / provenance evidence
  epochs/                        local immutable-artifact identity evidence
  projections/                   source -> hot projection mapping
```

The launcher selects the plane by command:

```text
frl runtime-*  -> control.whl
all other frl  -> current.whl
```

This separation was not part of the first implementation. It appeared after a failure biopsy: after rolling the app back, the second rollback was executed by the old runtime manager. The fix was to keep update/rollback/prune logic on an independent latest-known-good control plane.

## Candidate activation contract

A new source wheel is not switched in immediately.

The path is:

```text
isolated source build
    -> content-addressed source store
    -> selective hot-pyc projection
    -> candidate smoke
         cache-doctor
         cache-analyze
         runtime-status
    -> manifest / smoke epoch
    -> atomic current/control switch
```

The previous app artifact remains available for rollback.

A fresh new-version activation is intentionally more expensive than reactivating an already verified immutable artifact. The latest measured fresh activation was approximately 0.44 s end to end, dominated by projection construction plus the three independent smoke processes. The atomic pointer switch itself was about 0.5 ms.

## Reinstall-loop evolution

The operational lane found several distinct stages.

| Stage | Observation |
|---|---:|
| repeated activation with full smoke | ~257 ms median |
| smoke epoch reuse | ~4.8-5.6 ms median |
| source/artifact identity epoch | ~0.95 ms median |
| identity epoch + separated control plane | ~0.62-0.64 ms median |

The latest independent 30-loop operational benchmark reports:

- same-artifact reactivate median: **0.6437 ms**
- p95: **0.7715 ms**
- minimum: **0.6189 ms**
- maximum: **0.7969 ms**
- median pointer/switch bookkeeping: about **0.095 ms**
- source identity epoch reused: 30/30
- artifact identity epoch reused: 30/30
- smoke evidence reused: 30/30
- projection rebuild: 0/30
- app switch: 0/30
- control switch: 0/30
- launcher rewrite: 0/30

A separate 50-loop confirmation immediately before the final benchmark measured **0.6170 ms median / 0.7328 ms p95**.

Compared with the earlier repeated-full-smoke median of 257.08 ms, same-immutable-artifact reactivation improved by roughly **400x** while retaining the smoke result as epoch-bound evidence rather than deleting the safety check.

This comparison is specifically for reactivation of the same immutable source/artifact. It is not a claim that a never-before-seen version can be installed in under a millisecond.

## Hot projection search

### Wheel compression

Changing ZIP compression did not materially improve startup:

- default wheel: about 451 KiB;
- DEFLATE level 1: about 506 KiB;
- DEFLATE level 9: about 448 KiB;
- stored/uncompressed: about 1.58 MiB.

The uncompressed wheel increased size by roughly 3.5x for less than about 1 ms of useful startup improvement. Rejected.

### All-module bytecode

Precompiling every Python module improved startup, but the wheel grew to roughly 1.59 MiB. Rejected as a poor size/performance point.

### Selective hot bytecode

A small hot set won the Pareto comparison. The projection keeps normal `.py` source and adds adjacent hash-based `.pyc` only for the operational hot path.

The current hot set includes the entry point, CLI dispatch, cache operations, adaptive engine, simulator, and runtime controller. Current projected artifacts are roughly 0.5 MiB.

Measured progression included:

- source-wheel help: ~65.8 ms -> selective-hot ~60.0 ms;
- source-wheel cache doctor: ~104.3 ms -> selective-hot ~87 ms;
- source-wheel standard analyze: ~119.9 ms -> selective-hot ~102 ms.

Later installed measurements, which include the normal `frl` launcher, stabilized near:

- `frl --help`: **65.7 ms** median;
- `frl cache-doctor`: **88.9 ms**;
- standard `frl cache-analyze`: **104.9 ms**;
- `frl runtime-status`: **83.2 ms**.

The Python process/import path now dominates these command latencies. The internal adaptive query work itself is sub-millisecond for the common queries.

## Dependency isolation

The first CLI promotion exposed another real failure: `cli.py` imported the calculator module at startup, which imported pandas. On the current lightweight Python environment pandas is not installed, so even `cache-doctor` failed before reaching its dependency-free code.

The CLI was changed to capability-scoped lazy imports. As a result:

- cache/runtime commands do not require pandas, NumPy, or SciPy;
- analysis calculators still request those dependencies only when invoked;
- package-level adaptive-engine exports are lazy;
- general help no longer imports every subsystem.

This is both a performance improvement and a functional robustness improvement.

## Installed cache-engine benchmark

Final installed evidence: `evidence/FRL-REINSTALL-008/installed-cache-benchmark-final.json`.

For the 12,000-reference shifting-hotset trace:

- parity gate: **PASS**;
- scalar LRU+OPT anchor pair: **7.008 ms** median;
- adaptive anchor pair: **0.194 ms**;
- speedup: **36.0x**;
- scalar mixed capacity sweep: **33.848 ms**;
- adaptive mixed sweep: **0.964 ms**;
- speedup: **35.1x**;
- cached full LRU-curve lookup: **0.000165 ms**;
- adaptive full OPT curve: **16.18 ms**;
- fresh `PreparedTrace` construction: **1.44 ms**.

The installed engine returns the same LRU and OPT answers as the scalar references before these speedups are accepted.

## Rollback test

The control-plane split was exercised on the real installed runtime.

1. latest artifact was current/control;
2. `frl runtime-rollback` switched the app plane to the previous artifact;
3. `frl runtime-status`, routed through control, still used the latest runtime manager;
4. the previous app successfully ran `frl cache-doctor`;
5. a second `frl runtime-rollback` restored the latest app using the latest control plane;
6. verified smoke evidence was reusable on the roll-forward path.

Thus rollback no longer implies rollback of the update controller.

## Reachability prune

`frl runtime-prune` is dry-run by default. `--apply` removes only state unreachable from `current`, `previous`, and `control`, plus associated source/projection/manifest/epoch records.

During development, prune runs reclaimed approximately 1.40 MiB, 0.96 MiB, and 0.97 MiB of superseded generations while preserving current and previous.

Final store state after prune:

- runtime artifacts: **2**
- artifact bytes: **1,016,496**
- canonical source wheels: **2**
- source bytes: **914,233**
- `control.whl` shares the current artifact rather than duplicating payload bytes.

So the two-generation app + rollback source/artifact payload is about 1.93 MiB, excluding tiny metadata and the separately rebuildable native accelerator cache.

## Benchmark surface for future use

The ordinary repeatable commands are now:

```bash
# Functional / algorithm benchmark
frl cache-benchmark \
  --length 12000 \
  --universe 257 \
  --capacity-anchor 41 \
  --anchor-capacity 41 \
  --capacities 17,41,83,127 \
  --repeats 40 \
  --out evidence/cache-benchmark.json

# Installed runtime + reinstall benchmark
frl runtime-benchmark \
  --loops 30 \
  --process-repeats 20 \
  --out evidence/runtime-benchmark.json

# Runtime health / generation state
frl runtime-status

# Safe cleanup preview, then application
frl runtime-prune
frl runtime-prune --apply
```

## Convergence judgment

This operational reinstall lane is frozen at bounded convergence because:

1. same immutable artifact reactivation is below 1 ms median;
2. atomic pointer work is about one tenth of a millisecond;
3. repeated cryptographic reads and repeated smoke processes were replaced with identity/smoke epochs rather than removed;
4. selective hot bytecode dominates both source-only and all-module bytecode projections for the operational path;
5. ZIP compression experiments yielded negligible latency gains;
6. the fast dispatcher produced only low-single-digit-millisecond improvements after lazy imports/hot projection;
7. app rollback and update-control rollback were decoupled and physically exercised;
8. old runtime generations can be reclaimed without losing current or previous.

Further large latency reductions for one-shot `frl` commands would require retaining a resident process or daemon. That is a different RAM/latency Pareto point, not a strict improvement of the current zero-resident-between-commands surface.

## Frozen architecture

```text
                         +------------------------------+
                         | latest known-good control     |
frl runtime-* ---------->| control.whl                  |
                         +------------------------------+

                         +------------------------------+
frl cache-* ------------>| current.whl                  |
other normal commands -->| active app/data plane        |
                         +------------------------------+
                                      |
                                      v
                     content-addressed hot-pyc artifact
                                      ^
                                      |
                         canonical source wheel

previous.whl ------------------> one-step app rollback

native .so --------------------> optional rebuildable cache
```

The normal surface is now ordinary; the unusual machinery remains underneath it.
