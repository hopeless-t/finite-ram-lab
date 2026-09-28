# Bounce Handoff

> **Bounce ID:** B239
> **Status:** STRATA-006 EXPLICIT HOSTED LAUNCH

## Rehydration

Canonical predecessor: B238.

B238 required exactly one read of ordinary CI for implementation commit `65035dfc4d4e2f9e5ec4075dda84fc39807e69cc`.

## CI result

Run `36433776719` was read once in B239:

- status: completed
- conclusion: success

No second read was performed.

## Action

Created the explicit path-gated launch marker:

`launch/STRATA-006-v1.txt`

The launch preserves the frozen design:

- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 56 / 72 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot setting
- 48 total trials
- REC-001 26 records/trial

## Scientific discriminator

Primary transformed hypothesis:

`K + hot_anon ~= constant`

versus a fixed raw `K`.

Existing STRATA-004 hot=64 anchor remains prior evidence and is not rerun.

## Monte Carlo

Deferred until STRATA-006 produces physical observations.

## Next action

Discover/read the STRATA-006 run for this exact launch commit once.

- success -> fetch aggregate artifact once, validate all 48 trials, atomize results, and run pseudo-Council;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant;
- absent -> checkpoint EXTERNAL_WAIT without launching again.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
