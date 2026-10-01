# B464 — Active Experiment Runtime Contract v0.1

Status: **SOFTWARE DECISION CONTRACT / NO AUTONOMOUS PHYSICAL INTERVENTION**.

## 1. Why this exists

Finite RAM Lab now has two needs that must not be conflated:

1. run useful applications under finite-resource constraints;
2. deliberately perturb conditions to learn the system.

A memory/runtime optimizer and an experimental actuator may share machinery, but
their data have different semantics.

B464 therefore freezes three runtime modes.

## 2. Modes

### OBSERVE

No intervention.

The baseline plan is executed exactly as declared.

Receipt partition:

`OBSERVATIONAL`.

Purpose:

- measure natural workload behavior;
- collect a reference distribution;
- avoid feedback-induced confounding.

### OPTIMIZE

Choose a feasible plan that satisfies the frozen fidelity, latency, and useful-work
constraints.

v0.1 selection rule:

> minimize predicted peak bytes, then latency, then maximize useful work.

This is intentionally constraint-based rather than an arbitrary weighted score.

Receipt partition:

`OPTIMIZATION`.

### PROBE

Choose an intentional intervention to distinguish a named hypothesis.

A PROBE requires:

- explicit `hypothesis_id`;
- explicit allowlist of variables that may change;
- numeric bounds and/or enumerated allowed values;
- ordinary fidelity/resource constraints;
- at least one actual changed variable.

v0.1 selection rule:

> maximize expected information gain per predicted second inside the probe
> envelope.

Receipt partition:

`EXPERIMENTAL_INTERVENTION`.

## 3. Structural rule

The central integrity rule is:

```text
OPTIMIZE data
!=
PROBE data
!=
OBSERVE data
```

Every decision receipt carries a dataset partition.

An intentionally perturbed run must never silently enter the natural/optimized
performance population.

## 4. Intervention receipt

The v0.1 receipt records:

- mode;
- dataset partition;
- baseline plan ID;
- selected plan ID;
- whether an intervention occurred;
- hypothesis ID for PROBE;
- changed variables with before/after values;
- held-constant variables;
- predicted peak;
- predicted latency;
- useful-work estimate;
- expected information gain;
- selection rule;
- claim ceiling.

This makes the causal intent of a run machine-readable before execution.

## 5. Fail-closed probe envelope

PROBE does not accept arbitrary parameter mutation.

A candidate is ineligible when:

- it changes a variable not explicitly allowed;
- a numeric value lies outside the frozen range;
- an enumerated value is not allowed;
- the ordinary fidelity gate fails;
- the normal resource constraints fail.

This is the first actuator boundary.

It is a software decision boundary only; it does not itself grant OS or MVCA
execution authority.

## 6. Frozen dogfood fixture

The first fixture uses the B463 streamed CRT family and asks only whether changing
`tile_rows` is worth measuring.

Baseline:

- strategy = STREAMED_FOLD;
- lane_count = 7;
- tile_rows = 64.

Allowed PROBE variable:

- tile_rows in {32,64,128} and numeric range [32,128].

A deliberately tempting ALL_RESIDENT candidate carries higher synthetic
information gain but changes `strategy`, which is outside the envelope and must
be rejected.

This fixture tests the policy boundary, not a scientific claim about which tile
size is physically best.

## 7. Connection to active Finite RAM research

The runtime closes the conceptual loop:

```text
OBSERVE
  -> identify uncertainty
  -> PROBE inside a bounded envelope
  -> freeze evidence
  -> update model
  -> OPTIMIZE under the updated model
  -> OBSERVE again
```

The important point is that optimization and system identification now become
different modes of the same application rather than ad-hoc scripts.

## 8. Claim ceiling

**SOFTWARE_DECISION_CONTRACT_ONLY**

B464 does not yet:

- launch a memory-pressure intervention;
- modify memcg state;
- autonomously change runner configuration;
- learn a model from historical receipts;
- prove expected-information-gain estimates are calibrated.

## 9. Next edge

B465 should connect the decision receipt to one bounded GitHub Actions dogfood
workload.

The executor must:

1. consume an immutable decision receipt;
2. run only the selected allowlisted action;
3. emit observed telemetry separately from predicted fields;
4. retain the pre-execution decision receipt;
5. never let post-run observations rewrite the decision that produced that run.

That creates the first real:

`decision -> intervention -> telemetry -> next-run learning`

loop without contaminating causal provenance.
