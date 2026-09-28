# CURRENT

> **Latest bounce:** B222
> **Stage:** RESEARCH MAINLINE RESUMED / REC-002 RELAUNCH REQUESTED

## Recorder status

Recorder is now treated as **research-ready / fail-visible** for the current scope.

Accepted properties include:

- malformed evidence fails visibly;
- lifecycle corruption fails closed;
- clean incomplete runs remain explicitly incomplete;
- JSONL is canonical and SQLite is rebuildable;
- duplicate conflicts are explicit;
- evidence-path ownership is exclusive;
- deterministic corruption regressions exist;
- REC-003 Monte Carlo attack machinery exists.

REC-003 remains a sidecar hardening tool. A 100,000-world campaign is not required before returning to the research mainline.

## Research policy

Run experiments first. Repair Recorder defects when real workloads expose them. Every real counterexample becomes a deterministic regression before reuse.

See `docs/RECORDER-RESEARCH-READY-POLICY.md`.

## REC-002

A fresh REC-002 observer-effect relaunch has been requested by updating:

`launch/REC-002-v1.txt`

The first run `36419229167` remains invalid with zero valid measurement trials.

## Next action

Read the fresh REC-002 hosted run exactly once.

- success -> inspect aggregate artifact and canonicalize observer-effect findings;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect failure only and repair the exposed issue.

If REC-002 supports use of Recorder in this workload, proceed to STRATA-005 implementation/launch.

## Parent research state

STRATA-005 external-validity design remains frozen from B206.

## Authority boundary

Hosted research only.
No local-PC execution.
No STRATA-005 launch inferred from this checkpoint.
No memory-control policy authorized.
