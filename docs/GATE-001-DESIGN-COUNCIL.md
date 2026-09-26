# GATE-001 Design Council — Selective Semantic Action

> **Status:** CONVERGED / EMPIRICAL GATE DESIGN STUDY REQUIRED BEFORE NEW EXPERIMENT

## Question

After EXP-003 showed large net benefit from CORRECT_PAGEOUT in naturally misaligned states and large harm from WRONG_PAGEOUT in aligned states, what pre-intervention gate is worth testing next?

## Council result

Do **not** immediately launch another intervention experiment.

First use the fully randomized EXP-003 factorial to estimate the decision boundary for a minimal gate:

```text
ACT    = apply the already-frozen 16 MiB semantic PAGEOUT
NO-ACT = preserve NO_HINT fallback
```

The gate uses only two pieces of pre-intervention application information:

1. historical initial fault/touch order;
2. predicted future HOT identity.

No new kernel signal or stronger action is introduced.

## Gate rule

Historical residency cue:

```text
second-faulted region is favored
```

Predicted semantic state:

```text
predicted HOT == first-faulted  -> predicted mismatch -> ACT
predicted HOT == second-faulted -> predicted aligned   -> NO-ACT
```

When ACT is chosen, PAGEOUT targets the predicted semantic COLD region.

## Exact stale-signal mapping

With a binary HOT identity, an inverted/stale semantic signal produces different failure modes depending on the true state.

### True aligned

```text
true HOT = second-faulted
wrong prediction = first-faulted
gate sees "misaligned"
        ↓
ACT
        ↓
PAGEOUT predicted COLD = actual HOT
        ↓
WRONG_PAGEOUT
```

### True misaligned

```text
true HOT = first-faulted
wrong prediction = second-faulted
gate sees "aligned"
        ↓
NO-ACT
        ↓
NO_HINT fallback
```

Therefore the gate's false-positive harm and false-negative cost are empirically available from EXP-003 without inventing a new error model.

## Empirical policy primitives

For each runner block, derive total-work cost for:

- `A_N`: aligned + NO_HINT;
- `A_C`: aligned + CORRECT_PAGEOUT;
- `A_W`: aligned + WRONG_PAGEOUT;
- `M_N`: misaligned + NO_HINT;
- `M_C`: misaligned + CORRECT_PAGEOUT.

Let:

- (q) = prevalence of true misalignment;
- (a) = correctness of the predicted future HOT identity.

The selective gate cost is:

```text
L_gate(q,a)
=
(1-q) * [a*A_N + (1-a)*A_W]
+
q * [a*M_C + (1-a)*M_N]
```

Baselines:

```text
L_nohint(q)
=
(1-q)*A_N + q*M_N

L_always_correct(q)
=
(1-q)*A_C + q*M_C
```

## Empirical break-even accuracy

Define:

```text
H = A_W - A_N   # false-activation harm in aligned state
B = M_N - M_C   # correct-action benefit in misaligned state
```

For positive (H) and (B), the gate beats NO_HINT when:

```text
a >
(1-q)H
-----------------
(1-q)H + qB
```

This replaces VOI-001's simplified (a > 1-q/k) boundary with a boundary calibrated directly from EXP-003.

## Outcomes

Do not collapse to one metric.

Report two policy surfaces separately:

1. **arithmetic total-work cost** — tail-sensitive user-time quantity;
2. **mean log total-work cost / geometric ratio** — robust multiplicative quantity consistent with EXP-003 inference.

A gate is considered worth experimental validation only where both surfaces favor it over NO_HINT with bootstrap uncertainty supporting the direction.

## Scenario grid

Freeze:

```text
q = 0.10, 0.25, 0.50, 0.75, 0.90

a = 0.50, 0.60, 0.70, 0.80, 0.85,
    0.90, 0.925, 0.95, 0.975, 0.99, 1.00
```

Also solve the empirical break-even accuracy continuously for each q.

## Uncertainty

Use runner as the cluster.

Use 100,000 deterministic runner-cluster bootstrap resamples.

No synthetic Gaussian latency model.

The policy mixture itself is analytic; Monte Carlo is only for uncertainty propagation from the 16 observed runner blocks.

## Next experiment criterion

A new GATE-001 execution experiment is authorized for design only if the empirical policy study identifies a finite accuracy region where:

- selective gate beats NO_HINT;
- selective gate is competitive with or safer than ALWAYS_CORRECT;
- stale-signal false activation remains the dominant explicit Red-Team risk.

The experiment should then target points around the measured break-even boundary, not arbitrary accuracy levels.

## Non-goals

Do not:

- tune PAGEOUT range;
- add a stronger reclaim primitive;
- train an ML gate;
- infer production (q);
- claim deployability.

## Authority boundary

This Council authorizes an empirical gate-policy design analysis only.

It does not yet authorize GATE-001 execution.
