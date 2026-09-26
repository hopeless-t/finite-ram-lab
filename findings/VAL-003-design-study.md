# VAL-003 Tail Design Study

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36229489183

## Question

How much independent runner replication and within-runner repetition are needed to test the pre-registered >=500 ms catastrophic-stall endpoint?

## Rare-event Monte Carlo

The simulation used:

- runner-shared logit heterogeneity;
- arm-specific block variation;
- baseline catastrophic-event rates from 3% to 8%;
- target reductions including 5%→2.5% and 5%→1%;
- 10,000 simulated experiments per cell.

The computational screen used paired runner-block event-rate contrasts.

## Results

| Design | Blocks | Repeats/arm | Trials | Null FP | 5%→2.5% detect | 5%→1% detect | 3%→0.6% detect | 8%→1.6% detect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1_20x20 | 20 | 20 | 800 | 0.050 | 0.431 | 0.917 | 0.756 | 0.984 |
| D2_32x12 | 32 | 12 | 768 | 0.052 | 0.467 | 0.944 | 0.784 | 0.993 |
| D3_40x10 | 40 | 10 | 800 | 0.049 | 0.491 | 0.961 | 0.821 | 0.995 |
| D4_40x16 | 40 | 16 | 1280 | 0.047 | 0.663 | 0.995 | 0.947 | 1.000 |

## Pseudo-Council conclusion

Select **D3_40x10**:

    40 independent runner blocks
    10 CORRECT_PAGEOUT trials per block
    10 NO_HINT trials per block
    800 total trials

Reasons:

1. it is the smallest tested design that exceeded 95% screened sensitivity for the exploratory 5%→1% target under the worst modeled runner-heterogeneity setting;
2. compared with D2 it spends only 32 additional trials while increasing independent runner replication from 32 to 40;
3. D4 buys additional moderate-effect sensitivity but requires 60% more trials;
4. the study remains only moderately sensitive to a 5%→2.5% reduction, so a null result cannot establish equivalence.

## Final-inference consequence

With 40 blocks, exact enumeration of all `2^40` sign assignments is intentionally avoided.

The frozen confirmatory analysis will use:

    deterministic Monte Carlo sign-flip randomization
    draws = 1,000,000
    fixed seed

and report the Monte Carlo standard error of the p-value.
