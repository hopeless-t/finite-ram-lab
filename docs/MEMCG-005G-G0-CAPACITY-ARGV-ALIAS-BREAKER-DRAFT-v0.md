# MEMCG-005G-G0 Capacity/Argv Alias Breaker — Draft v0

> **Status:** DRAFT / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Goal

Determine whether the observed CAP8/9 vs CAP10+ exact-zero enrichment survives after removing capacity-dependent argv representation.

This experiment must run before the larger MEMCG-005G-G exact-zero replication.

## Primary change

Do not pass `--max-pages <decimal>`.

Extend the existing shared control page with:

`uint32_t max_pages_u32`

The controller writes the capacity before launching the worker.

Worker launch argv is capacity-independent:

- worker path
- `--shared <path>`

The worker reads `max_pages_u32`, validates it, then performs the anonymous mmap.

## Frozen capacity panel

`{8,9,10,11,12,32}`

Primary endpoint:

`ZERO_CAPTURE := first_touch_delta_pages == 0`

Q64 and nonzero anomalies remain separate endpoints.

## Address-layout receipts

Before READY, and before touching the anonymous region, publish through the already-faulted shared control page:

- `ctl_addr_u64`
- `region_addr_u64`
- `region_end_u64`

Derived analysis receipts:

- `region_addr_mod_2m`
- `region_pte_index = (region_addr >> 12) & 511`
- same-PTE-table indicator between control and region addresses where meaningful.

These are secondary explanatory diagnostics only.

## Gate

Retain REMOTE_LOW:

- startup P;
- measured S != P;
- `pre_current_pages <= 110`;
- Q64 = 60..68 pages;
- zero CPU mismatch.

## Candidate scale

Preferred alias-breaking discovery scale:

- 32 independent hosted blocks;
- 60 candidates/block;
- 10 candidates/arm/block;
- 1920 total candidates;
- 320 candidates/arm.

Planning simulation under 005G-F exact-zero rates:

- direction recovery ~=99.96%;
- Fisher p<.05 with correct direction ~=89%.

This is deliberately smaller than the 5760-candidate 005G-G confirmatory replication.

## Primary interpretation

### CAPACITY_SIGNAL_SURVIVES_ALIAS_BREAK

Require prospectively:

- pooled exact-zero rate CAP8+9 < CAP10+11+12+32;
- direction is consistent in a majority of block strata;
- no CPU mismatch;
- no gross admission imbalance attributable to capacity;
- exact-zero morphology reported separately from nonzero anomalies.

A full confirmatory threshold posterior is not required here.

### CAPACITY_SIGNAL_COLLAPSES_AFTER_ALIAS_BREAK

Use when the split materially collapses after capacity is removed from argv.

This would invalidate interpreting previous T10 evidence as a clean mapping-capacity effect.

### UNRESOLVED

Use otherwise.

## Secondary layout analysis

Test whether exact-zero capture varies with:

- `region_addr_mod_2m`;
- PTE index;
- distance from control mapping;
- whether first-touch allocation likely requires a different PTE page.

Any such relationship is exploratory and requires a later prospective test.

## Compute authority

Do not implement or launch until Human explicitly approves this hosted scale.

Do not launch the larger 5760-candidate MEMCG-005G-G first.

No local-PC execution.
