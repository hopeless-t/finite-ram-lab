# FRL-REINSTALL-006 Reprime / Eviction Result — 2026-10-12

Status: PILOT + CONFIRMATORY PASS / CONVERGENCE GATE PASS

## Question

Can resident execution state be discarded under finite-RAM pressure and reconstructed on the next request without making the cold path materially worse?

Each block uses the same input across three zero-resident starting states:

- `cold_exec`: execute directly in a fresh Python process;
- `warm_reprime`: start an imported persistent-worker image, execute its first request, then destroy it;
- `fork_reprime`: start an imported clean template, fork one disposable child, execute, then destroy the template.

No worker survives between blocks.

## Pilot — 30 blocks

| Arm | Median ready-to-result | Ratio vs cold |
|---|---:|---:|
| cold_exec | 49.729 ms | 1.000 |
| warm_reprime | 43.418 ms | 0.873 |
| fork_reprime | 45.601 ms | 0.917 |

All 30 semantic triplets matched.

## Confirmatory — 60 blocks

| Arm | Median ready-to-result | p95 | Ratio vs cold |
|---|---:|---:|---:|
| cold_exec | 49.516 ms | 50.362 ms | 1.000 |
| warm_reprime | 43.501 ms | 44.722 ms | **0.879** |
| fork_reprime | 45.611 ms | 46.385 ms | **0.921** |

All 60 semantic triplets matched. Canonical build residue delta remained 0 bytes.

The frozen convergence gate required at least one reprime path to be within 10% of cold-exec latency. Both reprime paths passed; in these measurements both were modestly faster.

This does not imply a universal performance advantage for a two-stage server startup. The important bounded result is that eviction did not create a worse cold path on this host and workload.

## Operational interpretation

Resident workers/templates are now optional performance caches:

- no memory pressure + minimum latency: keep `warm_persistent`;
- no memory pressure + strong per-request state reset: keep `fork_template`;
- memory pressure: destroy either immediately;
- next request after eviction: reprime from the verified wheel;
- artifact identity change: leave the epoch fast path and re-run full cryptographic verification.

The only mandatory persistent runtime object is the small verified artifact and its trust metadata. The ~18 MiB process image is reclaimable state.
