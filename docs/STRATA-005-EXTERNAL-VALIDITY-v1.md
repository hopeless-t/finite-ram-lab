# STRATA-005 External Validity Design v1

> **Status:** FROZEN DESIGN / NOT YET LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Does the DONTNEED pressure-event transition track available pressure headroom, rather than a fixed release interval?

## Parent evidence

STRATA-004 on GitHub-hosted Ubuntu 24.04 used MemoryHigh=160 MiB, 64 MiB hot anonymous memory, and a 96 MiB cold file. The observed transition was `80 MiB < knee <= 88 MiB`; 80 MiB already peaked near 157.86 MiB, so it is a boundary observation rather than a portable default.

## Minimal external-validity axis

Change **MemoryHigh only** while preserving runner, workload, hot anonymous allocation, cold-file size, read chunk, cold-file preparation, integrity checks, and DONTNEED implementation.

Proposed pressure settings:

- 144 MiB
- 176 MiB

Keep 160 MiB as the already-observed anchor; do not spend hosted budget repeating it in v1.

Use a small common cadence panel:

- buffered
- 48 MiB
- 64 MiB
- 80 MiB
- 96 MiB

The panel is intentionally coarse. This study asks whether the response surface moves with pressure headroom, not for another exact knee.

## Design

- 2 MemoryHigh settings
- 5 arms
- 4 independent runner blocks per setting
- 40 total new trials
- MemoryMax remains 320 MiB
- hot anonymous memory remains 64 MiB
- cold file remains 96 MiB

Primary outcomes remain:

- MemoryHigh event delta during scan
- maximum scan memory.current
- post-scan memory.current
- post-scan file residency

Secondary outcomes retain advice-call count, pgscan/pgsteal, retouch cost, swap, and throughput. Throughput remains descriptive only.

## Normalized analysis

For each trial derive:

- `release_fraction_of_high = release_interval / MemoryHigh`
- `peak_fraction_of_high = max_scan_memory_current / MemoryHigh`
- `headroom_over_hot = MemoryHigh - hot_anon`

The first external-validity question is whether pressure-event onset aligns more consistently in normalized coordinates than in raw MiB.

No controller formula is authorized from two new pressure settings.

## Pseudo-Council

- **Systems:** vary one causal axis first; changing runner substrate simultaneously would confound interpretation.
- **Statistics:** four blocks per cell are sufficient for directional external-validity screening, not precise threshold estimation.
- **OSS portability:** normalized coordinates are worth testing, but must not be promoted to a default from one runner family.
- **Economics:** 40 new trials is materially smaller than repeating another 64-trial refinement.
- **Safety/authority:** Proposal != Decision. Design freeze grants no launch, implementation, retry, or OSS-default authority.

Consensus: **freeze a cross-pressure study first; defer cross-substrate testing until the pressure-axis result exists.**

## Monte Carlo

Deferred. Before cross-pressure observations exist, assigning a distribution to knee movement would manufacture evidence.

## Launch boundary

This document freezes the study design only. A later bounce may implement the hosted workflow/spec. Launch remains a separate explicit action. No local-PC execution is authorized.
