# FR-NORTHSTAR-005 — Close the Transfer/Staging Gap

Status: **HOSTED-PROXY NORTH-STAR LOOP CLOSURE**

Parent: **FR-XFER-001**

## Why this lane matters

FR-NORTHSTAR-004 identified exactly one new capability gap:

`TRANSFER_STAGING_PRESSURE`.

FR-XFER-001 then ran the mechanism experiment selected by that gap.

This lane asks the question that the old research process often postponed:

> Did the experiment actually close the gap?

If yes, mechanism-specific transfer research should stop.

## Step 1 — capability gap

Before FR-XFER-001:

`TRANSFER_STAGING_PRESSURE -> CAPABILITY_GAP`.

There was no registered physical primitive for the problem.

## Step 2 — physical experiment

FR-XFER-001 measured a 32 MiB host-memory payload.

Baseline-subtracted PSS:

- source: 32,772 KiB;
- direct source + destination: 65,544 KiB;
- source + staging + destination: 98,316 KiB;
- source + shared view: 32,772 KiB.

Exact frozen ratios:

- direct/source = 2x;
- staged/source = 3x;
- shared/source = 1x.

## Step 3 — registry update

Two hosted-physical primitives are added:

### DIRECT_TRANSFER_NO_STAGING

Applicable only when:

- copy semantics are valid;
- an explicit staging copy is not required;
- payload size is known;
- memory budget is known.

### ZERO_COPY_SHARED_VIEW

Applicable only when:

- sharing semantics are compatible;
- source lifetime covers the consumer;
- aliasing is safe;
- memory budget is known.

Neither primitive is live-promotable from hosted evidence.

After registration alone, the gap becomes:

`MODEL_GAP`.

That is correct.

A physical mechanism exists, but a workload effect model is still needed.

## Step 4 — transfer-peak effect model

Synthetic fixture:

- current resident state: **560 MiB**;
- resident budget: **600 MiB**.

The source payload is already part of current residency.

Therefore the migration adds only the physical copies beyond SOURCE_ONLY.

### Explicit staged copy

Increment:

[
98316-32772=65544 KiB.
]

Predicted transient peak:

[
624.0078125 MiB.
]

Result:

**over budget**.

### Direct copy without staging

Increment:

[
65544-32772=32772 KiB.
]

Predicted peak:

[
592.00390625 MiB.
]

Result:

**qualified under the synthetic 600 MiB envelope**.

### Shared / zero-copy view

Increment:

[
32772-32772=0.
]

Predicted peak:

[
560 MiB.
]

Result:

**qualified**, if sharing semantics are legal.

## Gap lifecycle

[
oxed{
CAPABILITY_GAP
ightarrow
MODEL_GAP
ightarrow
FRONTIER_REACHED
}
]

That is the first complete North-Star research loop.

## Research stopping rule

The important output is not:

> zero copy is amazing, study it forever.

The output is:

> the transfer/staging capability gap is closed in the hosted proxy model.

Therefore:

[
oxed{
	ext{stop transfer-mechanism research}
}
]

unless a real causal workload trace produces a new transfer-specific frontier
miss.

The next action is either:

- host-bound qualification for a workload that needs the primitive; or
- return to the global gap selector.

## Why zero-copy is not a universal answer

A shared view can be illegal when:

- producer lifetime ends too early;
- consumer requires independent mutation;
- aliasing changes semantics;
- device/backend cannot consume the representation directly.

Therefore the compiler must treat zero-copy as an applicability-constrained
primitive, not a default optimization.

## Safety boundary

FR-XFER-001 is hosted physical evidence.

It is **not**:

- development-machine calibration;
- GPU DMA evidence;
- pinned-memory evidence;
- live execution authority.

Frozen live actions executed:

**0**.

## North-Star lesson

The shortest research path is now executable:

```text
frontier miss
   ↓
gap classification
   ↓
new experiment only for capability gap
   ↓
physical evidence
   ↓
primitive registry
   ↓
effect model
   ↓
re-evaluate frontier
   ↓
gap closed?
   ├─ yes -> STOP this research branch
   └─ no  -> diagnose again
```

This is the zero-base policy in operational form.

## Claim ceiling

**HOSTED_PROXY_NORTH_STAR_LOOP_CLOSURE_ONLY**
