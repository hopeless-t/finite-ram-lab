# B464 — Active Experiment Runtime Receipt

Status: **PASS / SOFTWARE DECISION BOUNDARY QUALIFIED**

## Frozen execution

- workflow run: 36927679468
- job: 110588927238
- execution head: 40e66ba66a920616b7c1d07c45fd404524143c44
- targeted tests: 6/6 PASS
- artifact ID: 11195100311
- artifact ZIP SHA256: 2465be374997cebd57367a271d352bc4104d815f58dae0a8cc37821c6aea2607
- decision receipt SHA256: 32f9c2967a1ddb88794ec6fdb231de52cfbfded64f4aa89c25fbd062baf42eb9

## Frozen PROBE decision

Mode:

`PROBE`

Dataset partition:

`EXPERIMENTAL_INTERVENTION`

Hypothesis:

`H464_TILE_GRANULARITY_INFORMATION`

Baseline:

`streamed_7_t64`

Selected:

`streamed_7_t32`

Changed variable:

```text
tile_rows: 64 -> 32
```

Held constant:

```text
lane_count = 7
strategy   = STREAMED_FOLD
```

A deliberately high-information candidate that changed `strategy` was rejected
because `strategy` was outside the probe envelope.

## Scientific value

B464 establishes a machine-readable separation between:

- passive observation;
- production-like optimization;
- intentional experimental intervention.

The important result is not that tile_rows=32 is physically best. Its information
gain values are a frozen software fixture.

The result is that the runtime can express:

> "change exactly this variable for this named hypothesis, hold these variables
> constant, and classify the resulting data as intervention data."

## Integrity rule

```text
OBSERVATIONAL
!=
OPTIMIZATION
!=
EXPERIMENTAL_INTERVENTION
```

A later analyzer must not pool these populations without an explicit model.

## Claim ceiling

**SOFTWARE_DECISION_CONTRACT_ONLY**

No physical condition was changed by B464 itself.

## Next

B465 must consume the immutable decision receipt and execute one bounded GitHub
Actions dogfood experiment.

The executor should:

- verify the decision receipt digest;
- enforce an allowlisted action surface;
- execute baseline and selected conditions in fresh processes;
- emit telemetry separately from prediction;
- keep the original decision unchanged;
- perform no same-run model update.

This will be the first closed-loop application step:

```text
decision receipt
-> intentional intervention
-> observed telemetry
-> evidence for a later run
```
