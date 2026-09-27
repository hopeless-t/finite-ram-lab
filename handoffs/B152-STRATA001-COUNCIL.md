# Bounce Handoff

> **Bounce ID:** B152
> **Status:** COMPLETE / STRATA-001 COUNCIL CONVERGED

## Decision

Open STRATA-001:

**Cold-file Page-Cache Bypass Preservation**

Inspired by:

- https://github.com/Niko1221/Strata
- observed upstream commit `8117643ccc68e3d08f80d38e064333742d4474bb`

## Attribution boundary

- explicit upstream credit added;
- no Strata source code copied;
- future source reuse requires separate license review.

## First causal question

Compare:

- MMAP;
- BUFFERED_PREAD;
- DIRECT_PREAD / O_DIRECT.

Ask whether bypassing page cache for intentionally COLD file data preserves intentionally HOT anonymous residency under the same finite memory budget.

## Sequence

1. capability probe;
2. bounded pilot;
3. Monte Carlo sizing;
4. confirmatory experiment.

No large experiment launch yet.

## Next action

Freeze the STRATA-001 capability/pilot contract and implement the smallest local/CI-safe probe.

## Parallel lane

LABEL-001 CI fix validation remains pending and is not silently discarded.

## Authority boundary

Independent bounded research only.
