# Fast Reinstall Loop — Convergence v3

Date: 2026-10-12
Status: OPERATIONAL ON GAYA-CENTRAL

v1 converged package/runtime projection. v2 increased analytical capability and compute performance. v3 promotes the result into the ordinary installed command surface.

## Current ordinary surface

```text
~/.local/bin/frl
```

Users do not need `PYTHONPATH=src` or an editable checkout to use the cache/runtime features.

## Current operating shape

- content-addressed source wheel;
- selective hot-pyc runtime projection;
- current app plane;
- previous rollback plane;
- separate latest-known-good control plane for `runtime-*`;
- smoke manifest/epoch;
- local immutable-artifact identity epoch;
- reachability prune;
- built-in cache and runtime benchmarks.

## Current measured floor

Same verified immutable source reactivation:

- 30-loop canonical installed benchmark: **0.644 ms median / 0.771 ms p95**;
- 50-loop confirmation: **0.617 ms median / 0.733 ms p95**;
- pointer bookkeeping: roughly **0.09-0.10 ms**.

Fresh never-before-seen versions still pay projection and smoke once. This is intentional.

## Capability/performance remains intact

Final installed cache benchmark:

- scalar anchor pair -> adaptive: **36.0x**;
- scalar mixed sweep -> adaptive: **35.1x**;
- semantic parity: PASS.

The operational promotion therefore did not trade away the v2 capability/performance gains.

## Storage bound

After reachability prune, the local rollback pool retains two app artifacts and two source wheels: about **1.93 MiB** payload total. The control plane points at the current artifact and adds no duplicate wheel payload.

## Stop condition

The reinstall surface is no longer the dominant cost. The remaining ~65-105 ms observed for one-shot CLI commands is primarily interpreter/process/import work. Eliminating that requires a resident worker, which spends RAM to buy latency and is therefore a new finite-RAM Pareto branch rather than a strict reinstall improvement.

For the zero-resident-between-commands operating mode, v3 is frozen.
