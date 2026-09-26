# Bounce Handoff

> **Bounce ID:** B085
> **Status:** COMPLETE / RECOVERY SEMANTICS CORRECTED

## Objective

Clarify what happens to useful work that exists after the last atomic checkpoint when a session is interrupted.

## Decision

Uncheckpointed work loses canonical authority but is not automatically erased.

New recovery classes:

- PROVISIONAL
- RECOVERABLE CANDIDATE
- UNRECORDED SIDE EFFECT

A later bounded recovery bounce may verify and promote surviving work.

External side effects must always be reconciled.

## Scientific state

Unchanged from B083.

## Next action

Snapshot the minimum empirical inputs for EXP-003 design Monte Carlo.

## Authority boundary

Operations only.
