# MATH-001 Model Competition over MEMCG-001 v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Goal

Make candidate laws compete on the same empirical event sequence.

The competition must not privilege Q=64.

Input:

`evidence/MEMCG-001/event-sequence-v1.json`

Source run:

`36449072026`

## Candidate model families

### NULL

No accounting jumps.

Expected to describe no-touch controls only.

### LINEAR

Baseline-corrected memory.current follows:

`y(n) = beta * n`

Fit beta by least squares.

Used as a smooth-accounting comparator.

### STAIRCASE(Q)

One stationary phase per trial:

`y(n) = Q * floor((n+s)/Q) - Q*floor(s/Q)`

Candidate:

`Q in {1,2,4,8,16,32,64,128}`

Fit integer phase `s in [0,Q-1]` by minimum full-sequence SSE.

### RESET_STAIRCASE(Q)

Negative memory.current discontinuities define observed reset boundaries.

Within each reset-delimited segment:
- preserve the observed segment baseline;
- fit an independent phase;
- keep one common Q.

The negative discontinuity itself is conditioned on as an observed reset event rather than explained by this model.

This tests whether a stable quantum survives a hidden-state reset.

### ARBITRARY_EVENTS

Observed positive event positions are encoded without periodic structure.

This can fit any event pattern but pays a combinatorial description-length cost.

## Full-sequence residual score

Reconstruct every trial's baseline-corrected current-page sequence from its event list.

For LINEAR, STAIRCASE and RESET_STAIRCASE report:
- SSE
- RMSE
- MAE
- maximum absolute residual

The primary residual comparison is touch trials.

## Combinatorial MDL position score

For each reset-delimited segment:

- segment has L eligible touch positions;
- observed positive-event set O has k events.

Arbitrary-position code:

`L_arbitrary = log2(C(L,k))`

For candidate Q and phase p:
- predicted periodic position set P;
- extras = O - P;
- misses = P - O.

Periodic position code:

`L_Q = log2(Q) + log2(C(L, |extras|)) + log2(C(L, |misses|))`

Interpretation:
- `log2(Q)` encodes phase;
- exception terms encode unexplained observed jumps and falsely predicted jumps.

For Q=1, phase cost is zero.

Q identity is selected from a fixed preregistered eight-value panel, so its constant model-ID cost does not affect ranking among Q candidates.

Report:

`MDL savings = L_arbitrary - L_Q`

Positive savings favors periodic structure.

## Held-out predictive competition

Leave one touch block out.

Training:
- choose Q minimizing reset-aware MDL over the other three touch blocks.

Held-out:
- reset boundaries are observable negative events;
- within each segment, reveal only the first positive jump to calibrate phase;
- predict all later periodic positive jumps using the trained Q;
- compare against later observed positives.

Report:
- precision
- recall
- F1
- exact-position error

Aggregate over four leave-one-block-out folds.

This specifically defeats divisor aliases:
- too-small Q predicts unobserved intermediate jumps;
- too-large Q misses real jumps.

## Regime-reset analysis

For each negative event:
- compare stationary-Q residual before/after;
- compare reset-aware-Q residual;
- report phase before and after reset.

A model that keeps Q stable but changes phase is interpreted as a latent-state/reset candidate.

## Secondary spectral diagnostic

For each reset-delimited segment compute candidate-frequency coherence:

`A(Q) = |sum_j exp(-2*pi*i*position_j/Q)| / k`

This tests phase concentration but is not allowed to select the fundamental Q alone because harmonics/divisors alias.

## Exact combinatorial sanity check

For clean four-jump / 256-step blocks, report conditional uniform-null probability that four arbitrary positions form an exact 64-spaced arithmetic progression:

`64 / C(256,4)`

This is only a sanity-check null, not a real-world causal p-value.

## Decision rule

### MODEL64_WINS

Only if all hold:

- RESET_STAIRCASE(64) has minimum total touch SSE among candidate Q;
- Q=64 has minimum total reset-aware periodic MDL among Q candidates;
- every leave-one-block-out fold trains to Q=64;
- aggregate held-out F1 for Q=64 is 1.0;
- controls do not exhibit a competing periodic event pattern.

### OTHER_Q_WINS

A different Q satisfies the same predictive/model-selection criteria.

### MIXED_MODEL

No single Q dominates both MDL and held-out prediction.

## Output

Hosted run emits:

- `model-competition.json`
- `model-competition.md`
- per-block residual/MDL tables
- held-out predictions

## Pseudo-Council

- **Statistics:** prediction outranks post-hoc fit.
- **Information theory:** shorter description is evidence for structure, not proof of mechanism.
- **Systems:** reset-aware segmentation matches the observed discontinuity without pretending to explain its cause.
- **Skeptic:** divisor/harmonic aliasing must be penalized by false predictions.
- **Authority:** mathematical selection does not authorize deployment.

Consensus:

**freeze MATH-001 as a preregistered model competition over existing empirical evidence.**

## Launch boundary

Design only.
No new physical experiment.
No local-PC execution.
