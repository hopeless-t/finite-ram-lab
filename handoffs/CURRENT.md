# CURRENT

> **Latest bounce:** B204
> **Stage:** STRATA-004 / IMPLEMENTED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Parent result

STRATA-003: 56 / 56 valid trials.

Observed pressure-avoidance bracket:

`32 MiB < knee <= 96 MiB`

## Frozen STRATA-004 study

See:

- `docs/STRATA-004-KNEE-v1.md`
- `specs/STRATA-004-KNEE-v1.json`

Arms:

- buffered
- DONTNEED 32 / 48 / 64 / 72 / 80 / 88 / 96 MiB

Design:

- 8 runner blocks
- 64 total trials
- workload shape unchanged from STRATA-003
- runner/kernel/cgroup provenance captured

## Launch

- launch commit: `4d22de0570030c987db3e76416c009e67c58341a`
- STRATA-004 hosted run: `36392457515`
- last observed status: `queued`
- ordinary CI run: `36392457516`
- last observed status: `in_progress`

One external status read has already been consumed for this turn.

## Next fresh-turn action

Read run `36392457515` exactly once.

- success -> inspect aggregate artifact once and canonicalize result
- pending -> checkpoint EXTERNAL_WAIT and stop
- failure -> inspect failure only; no blind retry

## Monte Carlo

Deferred until empirical transition localization is tighter.

## Authority boundary

Hosted research only.
No local-PC execution.
No retry/rerun inferred.
No OSS default cadence authorized.
