# FR-FP-058 Failure Biopsy — Floating Crossover Tie

Status: **NUMERICAL CONTRACT REPAIR / POLICY BOUNDARY UNCHANGED**

Failed qualification:
- workflow run: 37226659915
- job: 111507590785
- head: 7fd1c786151bb2fa40c8d314b24343c49d170a35

Observed:
- validation points: 50,020
- mismatches: 1
- mismatching rent: 0.07350214904258025
- direct: P0
- compiled: P2

At that frozen crossover:

    score(P0) = 996.6180127733905 ms
    score(P2) = 996.6180127733907 ms

Difference:

    1.1368683772161603e-13 ms

This is floating-point representation noise, not a physical or policy
difference.

## Repair

Do not move the crossover.

Define a canonical score-tie contract:

    abs(score - minimum) <= 1e-9 ms

is decision-equivalent.

Within that numerical tie:
1. prefer lower resident MiB-round;
2. then stable path ID.

The compiled interval already uses the lower-residency path on the exact
crossover via right-inclusive transition semantics.

## Why 1e-9 ms

The tolerance is orders of magnitude below the physical timing resolution of the
hosted experiments and only resolves arithmetic representation noise.

It is not a scientific slack variable and must not be used to merge materially
different policies.

## Compiled lesson

**EXACT_DECISION_BOUNDARIES_REQUIRE_AN_EXPLICIT_NUMERICAL_EQUIVALENCE_CONTRACT;
DO_NOT_MOVE_A_PHYSICAL_CROSSOVER_TO_HIDE_FLOATING_POINT_NOISE.**

Claim ceiling:

**FP058_FLOATING_CROSSOVER_TIE_REPAIR_ONLY**
