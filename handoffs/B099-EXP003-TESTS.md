# Bounce Handoff

> **Bounce ID:** B099
> **Status:** COMPLETE / EXP-003 TESTS ADDED

## Objective

Add only known-answer and deterministic schedule tests for the frozen EXP-003 implementation.

## Completed

- `tests/test_exp003.py`

Tests cover:

- 24-cell complete factorial schedule;
- 12 aligned / 12 misaligned cells per block;
- deterministic block schedules;
- known-answer one-sided exact sign-flip for benefit and harm directions.

## Next action

Observe ordinary CI for this implementation in a fresh bounce.

Do not create the experiment workflow unless CI passes.

## Authority boundary

Tests are implementation validation only.
