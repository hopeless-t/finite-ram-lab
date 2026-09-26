# EXP-003 Design Monte Carlo — Initial Result

> **Status:** COMPUTATION PASS / FROZEN RULE SELECTS D1
> **Run:** 36253106666

## Design table

| Design | Blocks | Complete repeats | Total trials | Null FP | 25% capture | 50% capture | 75% capture | Eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| D1_16x1 | 16 | 1 | 384 | 0.043 | 0.999 | 1.000 | 1.000 | YES |
| D2_24x1 | 24 | 1 | 576 | 0.049 | 1.000 | 1.000 | 1.000 | YES |
| D3_32x1 | 32 | 1 | 768 | 0.048 | 1.000 | 1.000 | 1.000 | YES |
| D4_16x2 | 16 | 2 | 768 | 0.040 | 0.999 | 1.000 | 1.000 | YES |
| D5_24x2 | 24 | 2 | 1152 | 0.042 | 1.000 | 1.000 | 1.000 | YES |

## Frozen selection rule

Eligibility required:

- null false-positive <= 0.065;
- 25% capture detection >= 0.70;
- 50% capture detection >= 0.90.

All five designs satisfy the rule.

Tie-break:

1. minimum total trials;
2. then more independent blocks.

Therefore the frozen rule selects:

> **D1_16x1 — 16 independent runner blocks × 1 complete 24-cell repeat = 384 trials.**

## Interpretation boundary

This is design support, not EXP-003 scientific evidence.

The simulation uses HYP-003 empirical block structure for benefit power.

EXP-002 wrong-action stress remains separate calibration and is not pooled into the benefit simulation.

## Next review

Before freezing the experimental contract, read the structured design artifact once to retain the Red-Team/action-cost calibration and verify it does not reveal a design-contract contradiction.
