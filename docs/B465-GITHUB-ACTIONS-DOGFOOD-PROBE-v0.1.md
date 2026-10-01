# B465 — GitHub Actions Dogfood Probe Executor v0.1

Status: **BOUNDED DECISION -> INTERVENTION -> TELEMETRY DOGFOOD**.

## 1. Goal

B464 produced a machine-readable PROBE decision but intentionally did not change a
physical execution condition.

B465 consumes that decision as an immutable input and executes the declared
intervention on GitHub Actions.

This is the first application-shaped loop in the Finite RAM program.

## 2. Frozen causal boundary

The B464 decision receipt is regenerated before execution and must have exact
SHA256:

`32f9c2967a1ddb88794ec6fdb231de52cfbfded64f4aa89c25fbd062baf42eb9`.

The executor refuses to run when the digest differs.

The receipt declares:

- mode = PROBE;
- partition = EXPERIMENTAL_INTERVENTION;
- hypothesis = H464_TILE_GRANULARITY_INFORMATION;
- baseline tile_rows = 64;
- selected tile_rows = 32;
- lane_count = 7 held constant;
- strategy = STREAMED_FOLD held constant.

B465 allows exactly that one-variable intervention.

## 3. Allowlisted execution surface

The executor reconstructs the baseline and selected variable maps from the frozen
receipt.

Allowed variable surface:

- strategy;
- lane_count;
- tile_rows.

For this B465 action the changed-variable list must be exactly:

`tile_rows`.

Additional changes fail closed.

Allowed tile rows:

- 32;
- 64;
- 128.

Allowed strategies:

- ALL_RESIDENT;
- STREAMED_FOLD.

The frozen decision itself holds strategy constant at STREAMED_FOLD.

## 4. Physical dogfood workload

The executor reuses the B463 numerical workload:

- exact rank-1 residue GEMM;
- seven residue lanes;
- incremental CRT reconstruction;
- exact output digest;
- normalized VmHWM growth;
- work-time measurement.

B465 runs four matched pairs.

Order alternates:

```text
baseline -> selected
selected -> baseline
baseline -> selected
selected -> baseline
```

Every arm is a fresh process.

## 5. Telemetry receipt

The output artifact is not a rewritten decision.

It is a separate telemetry receipt carrying:

- decision receipt SHA256;
- hypothesis ID;
- selected and baseline IDs;
- declared changed/held variables;
- observed per-arm telemetry;
- paired peak deltas;
- paired latency ratios;
- semantic-match count;
- explicit `same_run_model_update=false`.

The decision that caused the run remains frozen.

## 6. Why same-run learning is forbidden

The first dogfood loop stops at telemetry.

```text
decision(N)
  -> intervention(N)
  -> telemetry(N)
  STOP
```

A later run may consume telemetry(N) to create decision(N+1).

This prevents the experiment from changing its own treatment after seeing its
outcome and then presenting the adaptive path as a predeclared comparison.

## 7. Scientific interpretation

B465 is useful even if tile_rows 32 and 64 have nearly identical performance.

The primary result is whether the application can:

1. freeze causal intent;
2. change only the declared condition;
3. run a real workload;
4. preserve correctness;
5. emit provenance-complete telemetry;
6. keep intervention data separate from optimization/observation data.

The physical tile-size effect is a secondary first specimen.

## 8. Claim ceiling

**BOUNDED_GITHUB_ACTIONS_DOGFOOD_PROBE**

This does not yet establish:

- an optimal tile size;
- calibrated expected information gain;
- autonomous experiment design;
- a production memory governor.

## 9. Next edge

If the dogfood executor passes, B466 should be the first next-run learner.

It should read a previous telemetry artifact and produce a new proposal without
executing it.

That would make the loop:

```text
run N telemetry
-> offline analyzer
-> run N+1 frozen decision
-> bounded executor
```

Only after that separation is stable should automatic multi-run scheduling be
considered.
