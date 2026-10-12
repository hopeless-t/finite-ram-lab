# FRL-REINSTALL-005 Template Projection — 2026-10-12

Status: LOCAL 60×3 PAIRED PASS

## Question

Can an imported process image remain resident as a clean template while every request executes in disposable state?

## Arms

- `cold_exec`: fresh interpreter/import/process per request.
- `warm_persistent`: one process performs all requests.
- `fork_template`: an imported parent remains idle; each request forks a child, computes there, returns the result, and exits.

A mutable request counter was deliberately added outside the semantic hash. It detects cross-request mutable-state retention.

## Result

| Arm | Median | p95 | Resident/peak memory | Counter behavior |
|---|---:|---:|---:|---|
| cold_exec | 50.952 ms | 52.460 ms | 18,868 KiB peak | always 1 |
| warm_persistent | 12.159 ms | 12.624 ms | 19,016 KiB parent | advances |
| fork_template | 14.293 ms | 14.974 ms | 18,296 KiB parent; child max-RSS median 12,840 KiB | **always 1** |

All 60 semantic triplets matched.

Speedup versus cold:

- warm persistent: **4.19x**
- fork template: **3.56x**

## Interpretation

The fork-template arm preserves most of the warm-worker speed while restoring per-request state destruction. Mutable process state created by one child cannot contaminate the next child because the template parent never performs the request workload.

This gives two non-dominated operating points:

- fastest: warm persistent;
- stronger state reset: fork template, about 2.13 ms slower per request.

Both spend roughly 18 MiB of idle resident memory, so a finite-RAM controller should treat the resident template as an evictable cache rather than mandatory state.
