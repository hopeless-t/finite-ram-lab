# Bounce Handoff

> **Bounce ID:** B229
> **Status:** STRATA-005 EXPLICIT HOSTED LAUNCH

## Predecessor

B228: `4389a0e520982f911b0dc82029d7e97130c7d802`

B228 recorded the Naive-N0.5-Flash source intake and accepted ordinary CI run `36428893054` as success after exactly one read.

## Action

Created the explicit path-gated launch marker:

`launch/STRATA-005-v1.txt`

This push is intended to start the existing frozen STRATA-005 workflow. No workflow definition, study spec, Recorder density, arm, pressure level, or acceptance rule is changed by this bounce.

## Frozen study

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- blocks: 4 per pressure
- total trials: 40
- REC-001 records: 26 per trial

## Next action in this bounce family

Discover the external run once for this exact launch commit.

- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- success -> collect artifacts once and atomize evidence;
- failure -> inspect the exposed invariant only and do not blind-rerun.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
