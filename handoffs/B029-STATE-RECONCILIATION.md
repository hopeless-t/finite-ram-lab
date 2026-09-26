# Bounce Handoff

> **Bounce ID:** B029  
> **Status:** COMPLETE / STATE RECONCILED

## Objective

Reconcile repository state after a stale rehydration attempted to repeat ENV-004 even though the canonical project had already advanced through EXP-002 and VAL-003 design.

## What happened

The worker initially rehydrated from B012 instead of the newest repository handoff.

That stale context produced a duplicate ENV-004 implementation and run:

- stale duplicate run: `36231647998`;
- stale duplicate head: `30c9ada7eafd5c33b783d75ddbef1a24aa914347`.

The duplicate run completed successfully but is **NON-CANONICAL** and must not be used as research evidence.

## Reconciliation

The canonical pre-existing ENV-004 files were restored from repository state before the stale duplicate:

- `specs/ENV-004.json`;
- `docs/ENV-004.md`;
- `.github/workflows/env-004.yml`.

Stale duplicate-only files were removed:

- `src/finite_ram_lab/env004_probe.py`;
- `src/finite_ram_lab/env004_study.py`;
- `tests/test_env004.py`.

## Canonical current research state

The latest valid research chain is:

```text
EXP-002
  ↓
central-tendency benefit not supported
wrong-hint harm strongly confirmed
  ↓
exploratory catastrophic-tail signal
  ↓
VAL-003 rare-event design Monte Carlo
  ↓
D3_40x10 frozen
```

Canonical VAL-003 design:

- 40 independent runner blocks;
- 10 CORRECT_PAGEOUT trials per block;
- 10 NO_HINT trials per block;
- 800 total trials;
- pre-registered catastrophic endpoint: HOT-retouch >= 500 ms;
- deterministic Monte Carlo sign-flip inference with 1,000,000 draws;
- cluster bootstrap over runner blocks.

## Canonical inputs for next bounce

- `handoffs/B028-VAL003-DESIGN-LAUNCH.md`
- `findings/VAL-003-design-study.md`
- `docs/VAL-003-DESIGN.md`
- `specs/VAL-003.json`
- `findings/EXP-002-initial.md`

## Next recommended bounce

> Implement and launch VAL-003 exactly as frozen. Do not modify the 500 ms endpoint after data collection begins.

## Authority boundary

The stale duplicate ENV-004 run is audit history only and carries no canonical research authority.

## Protocol lesson

At every fresh bounce, discover the **highest current handoff ID from the repository** before reading any older handoff.

Repository chronology wins over chat chronology.
