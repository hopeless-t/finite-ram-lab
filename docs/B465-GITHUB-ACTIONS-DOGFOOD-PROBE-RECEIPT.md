# B465 — GitHub Actions Dogfood Probe Receipt

Status: **PASS / FIRST BOUNDED DOGFOOD INTERVENTION EXECUTED**

## Frozen execution

- workflow run: 36928124977
- job: 110590394552
- execution head: 7cc8389f4cb6efc2429e84e9b9a1f95fa8dd6982
- targeted tests: 5/5 PASS
- artifact ID: 11195280298
- artifact ZIP SHA256: 6f0d257c38c37d16469d5cb464bc1c341fa3fdc58a20b0178ce14c0f1c438334
- decision receipt SHA256: 32f9c2967a1ddb88794ec6fdb231de52cfbfded64f4aa89c25fbd062baf42eb9
- telemetry SHA256: 3d02cd3269e21b14b2d7a7a6291a59308be106c7860af5013b647f4a7512f92f

## Provenance

Mode:

`PROBE`

Partition:

`EXPERIMENTAL_INTERVENTION`

Declared intervention:

```text
tile_rows: 64 -> 32
```

Held constant:

```text
lane_count = 7
strategy   = STREAMED_FOLD
```

The regenerated decision receipt matched the B464 frozen digest exactly before
execution.

No same-run model update occurred.

## Semantic result

All four matched pairs preserved exact numerical semantics.

```text
semantic_match = 4/4
```

## Peak result

Selected minus baseline normalized peak growth:

```text
     0 B
 +4,096 B
-81,920 B
 -4,096 B
```

Summary:

- negative = 2/4
- positive = 1/4
- zero = 1/4
- median = **-2,048 B**

This is not a replicated peak reduction.

Classification:

**PEAK_EFFECT_UNRESOLVED_WITH_LATENCY_COST**

The correct interpretation is that the tile-row change produced no robust peak
signal at this scale in the first bounded panel.

## Latency result

Selected/baseline ratios:

```text
1.01988
1.01179
1.02442
1.00741
```

Median:

**1.01584**

Observed median latency penalty for tile_rows 32 relative to 64:

**+1.58%**

This small panel does not establish a universal penalty, but there is no evidence
here that the smaller tile paid for itself with a robust peak reduction.

## Why this is a valuable negative/ambiguous result

The application worked as an experimental actuator.

It:

1. froze a decision before execution;
2. verified the decision digest;
3. changed exactly one allowed variable;
4. ran real numerical work in fresh processes;
5. preserved exactness;
6. separated telemetry from prediction;
7. did not alter its own model after seeing the result.

The first probe therefore falsifies the tempting simplistic rule:

> smaller reconstruction tile automatically yields a meaningful lower process peak.

At least for this geometry, that rule is unsupported.

## Claim ceiling

**BOUNDED_GITHUB_ACTIONS_DOGFOOD_PROBE**

No optimal tile size is established.

## Next

B466 should run offline, consume this frozen result, and produce a next-run proposal
without executing it.

A reasonable next exploration is the opposite side of the frozen tile envelope:

`tile_rows 64 -> 128`

because the 32-row direction yielded little peak information and a small latency
cost.

That proposal must remain separate from B465 evidence and must carry the B465
telemetry digest as provenance.
