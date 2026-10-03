# FR-FP-018 — Order-only Monte Carlo null

Status: **FROZEN TRACE MONTE CARLO CANDIDATE**

Parent: **FR-FP-017**

## Question

FR-FP-017 observed a heavy COLD tail, but the slow events were isolated rather
than contiguous.

The next question is not whether COLD is variable.

That is already established.

The question is:

> does the observed temporal order contain more structure than a random ordering
> of the exact same latency multiset?

## Frozen evidence

No new physical restore is performed.

The exact 48 WARM + 48 COLD trace from FR-FP-017 is frozen under data/.

This lane changes only temporal order.

Therefore every shuffle preserves:

- sample count;
- latency marginal distribution;
- 25 ms miss count;
- min/max;
- all latency values.

## Null

For each arm independently:

- 20,000 deterministic random shuffles;
- frozen seed;
- recompute temporal metrics.

Predeclared metrics:

1. absolute lag-1 autocorrelation;
2. absolute lag-2 autocorrelation;
3. absolute lag-4 autocorrelation;
4. max >25 ms run, upper tail;
5. max >25 ms run, lower tail;
6. four-epoch >25 ms miss-count range;
7. four-epoch median-latency range.

Familywise alpha:

    0.05 / 7

by Bonferroni correction.

## WARM is a control

The same order test is applied to WARM.

Routing logic:

COLD significant, WARM not significant
: candidate COLD-specific temporal structure.

WARM significant
: suspect shared environment, harness periodicity, or runner-level state before
  attributing the effect to the COLD tier.

Neither significant
: do not fit a within-run latent-state model from this trace.

## Important non-goal

This experiment does not test cross-run nonstationarity.

FR-FP-016 already established strong cross-run COLD regime variation.

FR-FP-018 asks only whether one long run contains additional order structure
beyond its own marginal distribution.

## Claim ceiling

**ORDER_STRUCTURE_TEST_ON_ONE_FROZEN_48_SAMPLE_HOSTED_TRACE_ONLY**
