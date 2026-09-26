# Bounce Handoff

> **Bounce ID:** B024  
> **Status:** COMPLETE

## Objective

Freeze EXP-002 runner/repeat allocation from the design Monte Carlo.

## Evidence

- design run: `36228813323`;
- D3_20x6: null FP 0.051, material detection 0.779, strong detection 0.981;
- D4_24x4: fewer trials but lower material detection and would make exact final sign-flip substantially larger.

## Frozen decision

Use:

    20 runner blocks
    6 repeats / arm / block
    3 arms
    360 total trials

Primary contrast: CORRECT_PAGEOUT vs NO_HINT.

Red-Team contrast: WRONG_PAGEOUT vs CORRECT_PAGEOUT.

## Next recommended bounce

> Implement and launch EXP-002 exactly as frozen.

## Authority boundary

The design study allocates evidence; it does not establish semantic-information value.
