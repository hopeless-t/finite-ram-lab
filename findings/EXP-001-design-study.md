# EXP-001 Design Study

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36228047531

## Question

How many independent hosted-runner blocks and within-block repeats are needed for the matched residency-identity intervention?

## Monte Carlo

The design study used the planned exact block-level sign-flip inference and stressed candidate designs under moderate, heavy, and branchy log-latency noise.

3,000 simulated experiments were run per design × scenario × effect cell.

## Result

| Design | Blocks | Repeats/arm | Trials | Worst null FP | Worst 2x detect | Worst 5x detect | Worst 20x detect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1_6x2 | 6 | 2 | 24 | 0.033 | 0.212 | 0.730 | 0.986 |
| D2_8x2 | 8 | 2 | 32 | 0.051 | 0.411 | 0.967 | 1.000 |
| D3_8x3 | 8 | 3 | 48 | 0.045 | 0.492 | 0.991 | 1.000 |
| D4_12x2 | 12 | 2 | 48 | 0.054 | 0.618 | 1.000 | 1.000 |

## Pseudo-Council conclusion

Select **D2_8x2**:

    8 independent runner blocks
    2 repeats per arm per block
    32 total trials

Reasons:

1. ENV-004 showed an extremely large intervention-fidelity contrast, so EXP-001 is primarily a large-effect causal bridge experiment.
2. D2 is the smallest candidate whose worst-case simulated detection rate exceeded 95% for a 5x latency effect.
3. Adding 16 more trials in D3 buys little additional sensitivity for the large-effect regime.
4. D4 is better for a 2x effect, but even D4 remains only moderately sensitive there; spending 48 trials would not turn a small-effect null into a strong equivalence claim.
5. If EXP-001 is null, the result must therefore be interpreted as ruling against a large causal effect, not proving equality.

## Frozen warning

The design is intentionally not an equivalence study.

A null result does not establish that residency identity has zero effect.
