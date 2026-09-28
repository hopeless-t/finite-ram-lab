# REC-002 Recorder Overhead Screening v1

> **Status:** FROZEN DESIGN
> **Authority:** HOSTED_RESEARCH_ONLY
> **Parent implementation:** REC-001 v0 at `496b0203c3075b22394aafdfb13ccb438d6331c5`
> **Parent CI:** run `36416819473` = SUCCESS

## Question

Does synchronous REC-001 JSONL recording materially perturb the near-boundary STRATA workload that it is intended to observe?

This is an observer-effect screening study, not a universal recorder benchmark.

## Why this condition

STRATA-004 observed that DONTNEED 80 MiB reached about 157.86 MiB under MemoryHigh=160 MiB while retaining median high-event count 0.

That makes the 80 MiB arm a deliberately sensitive boundary condition: a recorder that adds enough resident/writeback pressure or scheduling cost to move the regime should be easier to detect here than in a low-pressure workload.

## Frozen workload

Reuse the STRATA-004 workload shape:

- GitHub-hosted Ubuntu 24.04 runner family
- MemoryHigh = 160 MiB
- MemoryMax = 320 MiB
- hot anonymous memory = 64 MiB
- cold file = 96 MiB
- read chunk = 4 MiB
- DONTNEED interval = 80 MiB
- same cold-file preparation and integrity checks

## Arms

Two paired arms:

### recorder_off

Run the instrumentable workload with the REC-001 callback disabled.

### recorder_on

Use the same code path and imports, but enable synchronous REC-001 writes.

Recording density:

- one `run_start` record;
- one `memory.current` sample per scan checkpoint;
- one `run_end` record.

The 96 MiB / 4 MiB workload produces 24 scan checkpoints, therefore 26 raw records per recorder-on trial.

No SQLite ingest occurs inside the pressure-sensitive interval.

## Design

- 8 independent hosted runner blocks;
- both arms once per block;
- arm order randomized deterministically per block;
- 16 total trials.

Pairing within a runner block is intentional; runner-to-runner timing variability is expected to dominate small overhead effects.

## Primary outcomes

Per trial:

- MemoryHigh event delta during scan;
- maximum scan `memory.current`;
- scan elapsed time;
- recorder JSONL bytes written.

Secondary outcomes:

- post-scan `memory.current`;
- post-scan file residency;
- advice calls;
- pgscan / pgsteal;
- hot retouch cost.

## Interpretation

The study asks whether recorder-on shows an observable perturbation relative to recorder-off.

No fixed universal acceptable-overhead threshold is predeclared. Report paired differences and distributions rather than forcing a PASS from an arbitrary percentage.

A visible pressure-regime change (for example recorder-on introducing high events where paired recorder-off remains at zero) is a strong warning and blocks recorder-instrumented STRATA performance evidence until addressed.

If no material perturbation is observed in this workload, that supports use in the next hosted STRATA study only; it does not prove transparency on mobile, bare metal, or other write densities.

## Authority boundary

REC-002 may execute only on hosted research runners.

It does not authorize STRATA-005 launch, memory-control policy, local-PC execution, or a claim that REC-001 is universally measurement-transparent.
