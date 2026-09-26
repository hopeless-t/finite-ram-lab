# MC-001 — Synthetic Replacement Opportunity Map

> **Status:** IMPLEMENTED / DECISION SUPPORT

## Question

Across controlled synthetic access patterns, how large can the replacement-decision gap become between a simple online recency policy and an oracle with perfect future knowledge?

## Purpose

MC-001 does **not** model the Linux memory manager.

It asks a narrower question:

> Are there access regimes where additional information has measurable theoretical value?

The comparison is:

- **LRU** — online recency-only baseline;
- **OPT / Belady oracle** — perfect-future lower bound on faults for the same trace and capacity.

The gap is an opportunity bound, not a claim that an application/OS coordination layer can achieve OPT.

## Workload families

- `stable_hotset`;
- `sequential_scan`;
- `shifting_hotset`;
- `bursty`.

Each trial randomizes bounded trace parameters using a declared seed.

## Primary metric

```text
fault_rate_gap = LRU fault rate - OPT fault rate
```

Additional outputs include LRU/OPT fault rates, capacity, unique pages, trace length, and per-trial seed.

## Monte Carlo requirements

- deterministic seed derivation;
- independent shards;
- order-independent aggregation;
- bounded trace length and capacity;
- machine-readable per-trial evidence;
- summary percentiles by family.

## Interpretation boundary

A large gap means perfect future information could improve replacement on that synthetic trace.

It does not establish a Linux kernel defect, a real-application performance gain, sufficient application hints, or acceptable userspace control latency.
