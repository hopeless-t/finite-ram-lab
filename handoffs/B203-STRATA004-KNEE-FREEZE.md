# Bounce Handoff

> **Bounce ID:** B203
> **Status:** COMPLETE / STRATA-004-KNEE-v1 FROZEN

## Frozen contract

Canonical documents:

- `docs/STRATA-004-KNEE-v1.md`
- `specs/STRATA-004-KNEE-v1.json`

Frozen arms:

- buffered
- DONTNEED 32 MiB
- 48 MiB
- 64 MiB
- 72 MiB
- 80 MiB
- 88 MiB
- 96 MiB / end-of-stream

Design:

- 8 runner blocks
- 8 arms
- 64 total trials
- same 160 / 320 MiB cgroup limits
- same 64 MiB HOT anonymous guardrail
- same 96 MiB COLD file
- same 4 MiB reads and scan checkpoints

## External-validity trace

The next hosted implementation must capture kernel, OS, systemd and cgroup substrate metadata once per block.

This is provenance only, not a portability claim.

## Inference boundary

STRATA-004 may refine the tested pressure-avoidance bracket.

It may not select an OSS default cadence.

If the response is non-monotone, preserve AMBIGUOUS rather than forcing a threshold.

## Monte Carlo

Deferred until after empirical knee localization.

## Next action

Implement the frozen hosted study without modifying the historical STRATA-003 frozen contract.

## Authority boundary

Hosted research only.
No local-PC execution.
