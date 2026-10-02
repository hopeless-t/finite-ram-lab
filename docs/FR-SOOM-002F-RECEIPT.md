# FR-SOOM-002F — Observable-Only Dependence Qualification Receipt

Status: **PASS / SYNTHETIC OBSERVABLE DEPENDENCE INFERENCE VALIDATED**

## Frozen qualification

- workflow run: 37024008734
- job: 110893920151
- execution head: 2324f1877bce913d542326f5ac10b0d41d78df1e
- targeted tests: 7/7 PASS
- artifact ID: 11234395748
- artifact ZIP SHA256: d575b7c0014324625da412510504cfe25f9873eed7ad255ca279c0fe6e866613
- spec SHA256: 41e9f4b9896182e9ce62707fe3759725f693fcb89342a8f45f280ecd68f43898
- result SHA256: cf496d39effcd6c379a4d8741429ad6ae6cf2e48d32056253683f69bf596b79a

## Input restriction

The analyzer receives only:

- episode index;
- per-action late/timely outcome.

It does not receive:

- latent BAD labels;
- generating arm labels;
- synthetic pressure-state truth.

Therefore the dependence result is derived from observable outcome structure,
not from generator metadata.

## Matched marginal contract

Both synthetic traces contain:

- 16,384 episodes;
- three cooperative actions;
- exactly 164 late outcomes per action.

The per-action marginal failure prevalence is therefore identical.

## Frozen result

| metric | INDEPENDENT | SHARED_BAD |
|---|---:|---:|
| tail count per action | 164 | 164 |
| observed pair co-failure total | 5 | 492 |
| multi-action late episodes | 5 | 164 |
| mean pairwise phi | 0.000154 | 1.000000 |
| permutation-null p95 | 9 | 9 |
| permutation-null p99 | 11 | 11 |
| upper permutation p | 0.587 | 0.001 |
| classification | IID_COMPATIBLE | CROSS_ACTION_DEPENDENCE_EVIDENCE |

## Null construction

The null performs 999 deterministic independent circular shifts.

For each action, the shift:

- preserves its exact marginal late count;
- preserves its own within-action trace shape;
- destroys its alignment with other actions.

The test therefore asks whether cross-action co-failure is stronger than expected
after preserving each individual action trace.

## Primary finding

The shared trace is distinguishable from an independently aligned trace without
access to any latent failure-domain label.

Therefore, within this synthetic control:

`shared failure-domain evidence can be recovered from observable co-failure traces`.

The independent trace is classified only as:

`IID_COMPATIBLE`.

That wording is deliberate.

A non-significant dependence test does not prove independence.

## Architecture implication

Read-only shadow observations can now support a failure-domain evidence graph
before any intervention authority exists.

Candidate flow:

```text
shadow receipt history
      |
      v
timely / late action traces
      |
      v
observable dependence analyzer
      |
      v
failure-domain evidence graph
      |
      v
deadline-aware planner
```

This turns correlation structure into an explicit controller input.

## Why this matters for an earlyoom successor

A pressure controller should not count three actions as three independent
fallbacks merely because they have different names.

If historical receipts show that they fail together, the planner should discount
their joint redundancy and preserve a differently coupled emergency action.

This is a materially different control model from static victim scoring.

## Claim ceiling

**SYNTHETIC_OBSERVABLE_DEPENDENCE_INFERENCE_ONLY**

No live process was controlled.

The synthetic permutation threshold is not a production escalation rule.

## Next

FR-SOOM-002G should close the loop:

- infer dependence from prior observable traces;
- choose between cooperative plans using that inference;
- evaluate deadline success and semantic loss on future episodes.

The important endpoint is not classification accuracy alone.

It is:

`deadline-safe semantic loss after inference-informed planning`.
