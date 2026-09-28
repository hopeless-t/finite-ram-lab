# Bounce Handoff

> **Bounce ID:** B245
> **Status:** STRATA-007 EXPLICIT HOSTED LAUNCH

## Rehydration

Canonical predecessor: B244.

B244 required exactly one read of ordinary CI run `36435391877`.

## CI result

The run was read once in B245:

- head: `a1e3f4ab042d3272178c6f435b88f2d25a8c01de`
- status: completed
- conclusion: success

No second read was performed.

## Action

Created the explicit path-gated launch marker:

`launch/STRATA-007-v1.txt`

The launch preserves the frozen cross-image design:

- new runner: `ubuntu-26.04`
- anchor: existing Ubuntu 24.04 STRATA-004 evidence
- explicit Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 total new trials
- REC-001 density unchanged

## Portability discriminator

Prior Ubuntu 24.04 anchor:

`80 MiB < K <= 88 MiB`

and:

`144 MiB < K+hot <= 152 MiB`.

STRATA-007 asks whether Ubuntu 26.04 remains compatible with those transformed intervals.

## Monte Carlo

Deferred until cross-image physical evidence exists.

## Next action

Discover/read the STRATA-007 run for this exact launch commit once.

- success -> fetch aggregate artifact once, validate 24 trials, atomize results, and run pseudo-Council;
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
