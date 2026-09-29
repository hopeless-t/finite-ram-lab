# MATH-003 — Rare-State Harvesting Model

> **Status:** EXPLORATORY MATHEMATICAL RESULT
> **Input:** MEMCG-005G-A run `36563233676`
> **Purpose:** turn rare first-touch failures into testable harvesting hypotheses.
> **No causal claim. No K7 inference.**

## 1. Observed state counts

Among 406 valid REMOTE_LOW probes in MEMCG-005G-A:

- fresh first-touch Q64: **378 / 406 = 93.10%**
- depth-1 residual phenotype: **22 / 406 = 5.42%**
- deep residual phenotype (>1): **6 / 406 = 1.48%**

Conditional on failure (28 specimens):

- depth1: **22 / 28 = 78.57%**
- deep: **6 / 28 = 21.43%**

Observed deep depths:

`14, 34, 45, 45, 47, 48`

## 2. A single memoryless residual-depth model fits badly

Null M0:

residual depth R follows a single truncated geometric distribution on 1..64.

Maximum-likelihood geometric parameter:

`p_hat = 0.10934`

Log likelihood:

`-88.2402`

AIC:

`178.48`

Alternative descriptive hurdle model M1:

- point mass q at depth1;
- otherwise uniform deep tail on 2..64.

MLE:

`q_hat = 22/28 = 0.785714`

Log likelihood:

`-39.4070`

AIC:

`80.81`

Therefore:

`Delta AIC = 97.67`

in favor of the spike-plus-tail description.

Under the fitted geometric null, the implied depth1 probability is about 0.1094; observing at least 22 depth1 specimens in 28 has binomial tail probability approximately:

`1.4e-16`

This does **not** prove two causal mechanisms, but it strongly rejects a simple one-component memoryless geometric description.

Operationally, treating depth1 and deep as separate phenotypes is mathematically justified.

## 3. Natural deep-species enrichment hypothesis

Deep phenotype incidence among valid REMOTE_LOW:

### EARLY identity 0..7

`4 / 102 = 3.9216%`

### STEADY identity 8..31

`2 / 304 = 0.6579%`

Exploratory odds ratio:

`6.1633`

One-sided Fisher exact:

`p = 0.03710`

With independent Beta(1,1) priors:

- posterior median p_deep(EARLY) ≈ **4.52%**
- 95% interval ≈ **1.60%..9.65%**
- posterior median p_deep(STEADY) ≈ **0.876%**
- 95% interval ≈ **0.203%..2.35%**
- `P(p_EARLY > p_STEADY) ≈ 0.987`
- posterior median rate ratio ≈ **5.15**
- 95% ratio interval ≈ **1.23..26.47**

However the Beta(1,1) marginal-likelihood Bayes factor for two rates vs one shared rate is only:

`BF10 ≈ 0.397`

so the sparse-data evidence is prior-sensitive and not confirmatory.

### Harvesting interpretation

EARLY is a promising **enrichment stratum**, not an established cause.

Using posterior predictive Beta(5,99) for EARLY deep incidence:

- 95% probability of >=1 deep specimen requires about **83 valid EARLY LOW probes**
- 99% requires about **153 valid EARLY LOW probes**

Observed EARLY LOW admission was 102/192 = 53.125%.

At that admission rate, 83 valid EARLY LOW corresponds to roughly:

- **156 EARLY candidates**
- approximately **20 independent 8-candidate block starts**

For STEADY, the analogous 95% requirement is about **522 valid LOW probes**.

Thus current data suggest EARLY-only natural harvesting is roughly sixfold enriched per valid candidate, though only about twofold better per 32-candidate block because a block contains 8 EARLY but 24 STEADY positions.

## 4. Residual-stock state model

Let R be usable residual stock pages on S immediately before the target touch.

Idealized transition:

- R = 0 -> target touch requires fresh batch charge Q64;
- R > 0 -> target touch consumes one page and reports delta0;
- each subsequent fresh-page touch decrements R;
- when R reaches zero, the next touch produces Q64.

The biopsy estimator is:

`R_hat = first later Q64 touch index - 1`

subject to the caveat that unrelated refill/drain/uncharge activity may intervene.

## 5. Controlled induction / bait hypothesis

MEMCG-004 independently established the calibrated Q64 staircase:

fresh Q64 -> residual63 -> 63 stock-consuming touches -> next Q64.

Therefore a verified fresh primer can be used as a deterministic state constructor.

After a verified Q64 primer, perform a total of `b` page touches in that batch before the target is measured.

Under the ideal stock model:

`R_target = 64 - b`

and the target's biopsy depth should be:

`depth = 64 - b`.

Examples:

| bait touches b | predicted target depth |
| ---: | ---: |
| 16 | 48 |
| 17 | 47 |
| 19 | 45 |
| 30 | 34 |
| 50 | 14 |
| 63 | 1 |

Every observed deep phenotype in MEMCG-005G-A is therefore synthesizable by a specific controlled bait count.

Observed deep depths map to implied hidden post-refill consumption counts:

- depth48 -> b16
- depth47 -> b17
- depth45 -> b19
- depth45 -> b19
- depth34 -> b30
- depth14 -> b50

Four of six deep specimens correspond to b=16..19.

A post-hoc sliding-window scan under a deliberately simple uniform b null gives an approximate probability of **0.009** for some four-wide window containing at least four of six samples.

The uniform-null assumption is not mechanistically justified and the window was discovered post-hoc, so this is only a clue.

## 6. Rare-Pokemon hypotheses

### H-R1 — Natural enrichment

Fresh hosted block starts enrich deep residual states.

Prediction:
deep incidence among prospectively frozen EARLY positions exceeds STEADY.

Current status:
suggestive, not confirmed.

### H-R2 — Spike-and-tail state family

First-touch failure is not a single homogeneous residual process.

Prediction:
future biopsy sets continue to show a strong depth1 spike plus a minority deep tail.

Current status:
strong descriptive support; causal mechanism unknown.

### H-R3 — Partial-batch induction

Deep residual phenotypes can be deliberately constructed from a verified fresh Q64 state by consuming a fixed number of bait pages before the target.

Prediction:

`observed biopsy depth = 64 - bait_count`

for prospectively chosen bait counts.

This is the strongest route to turning a rare event into a controlled state.

### H-R4 — Natural deep specimens are hidden bait bursts

At least some natural deep specimens arise because unobserved S-side activity first creates a Q64 batch and consumes a discrete number of pages before the measured target touch.

Prediction:
instrumentation that catches pre-target S-side charge activity should show a burst whose net consumed count corresponds approximately to `64 - observed_depth`.

Current status:
mechanistic hypothesis only.

## 7. Required order of experiments

Before interpreting the elevated 005G-A failure rate, perform the already-frozen:

`MEMCG-005G-B CAP8 vs CAP70 footprint control`.

Only after that control should controlled induction be launched.

If footprint is not causal, the next positive-control experiment should prospectively choose bait counts:

`b = {16, 19, 30, 50, 63}`

predicting depths:

`{48, 45, 34, 14, 1}`.

Exact-depth recovery would validate the biopsy/state-transition instrument.

Failure of exact-depth recovery would falsify the simple induction model or expose additional asynchronous state transitions.

## 8. Application relevance

A successful controlled-induction result would change the research object from:

"rare accounting failure"

to:

"constructible CPU-local accounting state."

That would be the prerequisite for a future memory orchestrator to deliberately prepare, verify, and admit workloads into known memory-accounting phases rather than merely react to aggregate memory.current.

Hosted research only.
