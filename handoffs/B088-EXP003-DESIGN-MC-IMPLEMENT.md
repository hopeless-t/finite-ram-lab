# Bounce Handoff

> **Bounce ID:** B088
> **Status:** COMPLETE / EXP-003 DESIGN-MC IMPLEMENTED

## Objective

Implement only the frozen EXP-003 design Monte Carlo.

## Completed

- `src/finite_ram_lab/exp003_design_mc.py`
- `specs/EXP-003-DESIGN-MC.json`
- `tests/test_exp003_design_mc.py`
- `docs/EXP-003-DESIGN-MC.md`

## Frozen selection rule

Eligible only when:

- null FP <= 0.065;
- 25% capture power >= 0.70;
- 50% capture power >= 0.90.

Then choose minimum total trials, tie-breaking toward more independent blocks.

## Explicit non-work

The design Monte Carlo has not been launched.

No EXP-003 experiment allocation is frozen yet.

## Next action

Verify ordinary CI for this implementation. If PASS, launch only the design-MC workflow in the following bounce.

## Authority boundary

Implementation only.
