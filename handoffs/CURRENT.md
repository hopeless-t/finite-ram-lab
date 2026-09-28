# CURRENT

> **Latest bounce:** B235
> **Stage:** STRATA-005 PASS / EFFECTIVE-LIVE-SET HEADROOM MODEL
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## STRATA-005 canonical PASS

Hosted run:

`36431449193`

Launch SHA:

`9f0ed686406a49b42e14d855e3d941970e55c94d`

Aggregate artifact:

- `STRATA-005-EXTERNAL-VALIDITY-36431449193`
- artifact id `10973632531`
- digest `sha256:8702206b4cb645796f0c2ca17f60bc155898d380225f6216804b790396592554`
- trial count: 40
- execution status: PASS

## Onset evidence

- MemoryHigh 144 MiB: `64 < knee <= 80 MiB`
- MemoryHigh 160 MiB, STRATA-004 anchor: `80 < knee <= 88 MiB`
- MemoryHigh 176 MiB: `knee > 96 MiB`

A fixed raw-MiB knee cannot satisfy all three observations.

## Effective-live-set headroom interpretation

For `K = H - B`, all three observations are consistent with:

`B in [72, 80) MiB`

STRATA-005 DONTNEED cells have median post-scan resident floor approximately:

`76.72 MiB`

Accepted directional interpretation:

**pressure-event onset tracks remaining headroom above an effective live-set floor more plausibly than a universal fixed release cadence.**

This is not a controller formula or OSS default.

Full result:

`docs/STRATA-005-RESULT.md`

## Monte Carlo

Deferred. Current interval-censored aggregate evidence does not justify inventing a threshold-jitter distribution.

## Next fresh-bounce action

Freeze the next hosted design:

- hold MemoryHigh constant;
- vary hot/live resident set;
- preserve the same read/release mechanism;
- test whether knee shifts inversely with live-set size;
- reuse the 64 MiB hot-anon STRATA-004 anchor where valid;
- keep timing secondary.

Do not launch before design freeze and implementation validation.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state intake
- LLM-jp-4.1 local worker + state-lifetime dogfood

These are proposals, not current execution authority.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
