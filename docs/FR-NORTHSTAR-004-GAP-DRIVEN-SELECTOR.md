# FR-NORTHSTAR-004 — Gap-driven Experiment Selector

Status: **SYNTHETIC RESEARCH ROUTER**

Parent: **FR-NORTHSTAR-003**

## Why this is the zero-base pivot

The biggest risk after discovering many useful memory atoms is not technical.

It is **research sprawl**.

A frontier miss can tempt the lab to invent another mechanism even when the
real problem is only:

- missing evidence;
- missing calibration;
- a too-expensive contract;
- or a primitive that already exists but has not been modeled.

FR-NORTHSTAR-004 makes that distinction explicit.

## Gap classes

### EVIDENCE_GAP

A currently registered, modeled primitive could close the North-Star gap if its
applicability preconditions were known.

Action:

`MEASURE_MISSING_PRECONDITIONS`.

Do **not** invent a new mechanism.

### MODEL_GAP

A registered primitive appears applicable, but the compiler lacks a qualified
effect model.

Action:

`QUALIFY_EFFECT_MODEL`.

Again, do **not** invent a new mechanism.

### CAPABILITY_GAP

No current registered/effect-modeled primitive can attack the binding failure
domain sufficiently.

Action:

`OPEN_NEW_MECHANISM_LANE`.

This is the normal justification for new mechanism research.

### CONTRACT_GAP

Known actions can hit the memory budget only by violating:

- quality;
- reliability;
- latency;
- CPU;
- IO;

or another task contract.

Action:

`FIND_LOWER_COST_COMPOSITION_OR_REVISIT_CONTRACT`.

A raw RAM reduction is not promoted as success.

### FRONTIER_REACHED

Existing actions already satisfy the target.

Action:

`NO_NEW_RESEARCH`.

Move to causal replay or host-bound qualification.

## Frozen five-case panel

The synthetic panel contains one case for each state.

### Evidence gap

MULTIWORKER_LLM has all major failure-domain evidence except the applicability
proof for immutable sharing.

If that evidence were collected, the existing primitive set could close the
600 MiB target.

Classification:

**EVIDENCE_GAP**.

### Model gap

A multi-tier pressure case sees `SEMANTIC_TIER` as an applicable registered
primitive, but FR-NORTHSTAR-003 has no quantitative shadow effect model for it.

Classification:

**MODEL_GAP**.

### Capability gap

A synthetic `TRANSFER_STAGING_PRESSURE` domain currently has no registered
primitive.

Classification:

**CAPABILITY_GAP**.

This is the one case in the frozen panel that is allowed to open a new
mechanism lane.

### Contract gap

LONG_CONTEXT can fit a 950 MiB target with quantization, but a frozen quality
floor of 0.995 rejects the synthetic quantized candidate.

Classification:

**CONTRACT_GAP**.

### Frontier reached

MULTIWORKER_LLM with complete causal applicability evidence for the current
core primitives reaches the 600 MiB target.

Classification:

**FRONTIER_REACHED**.

No new mechanism research is justified.

## Frozen result

Five cases.

Only **1 / 5** produces:

`OPEN_NEW_MECHANISM_LANE`.

That is the key result.

The selector turns "we missed the target" from a research invitation into a
diagnostic question.

## The new research loop

```text
task contract
    ↓
causal observation
    ↓
shadow compiler
    ↓
frontier miss?
    │
    ├─ no  -> qualify / promote evidence
    │
    └─ yes
         ↓
      gap selector
         ├─ EVIDENCE -> measure
         ├─ MODEL    -> model
         ├─ CONTRACT -> cheaper composition / explicit contract review
         └─ CAPABILITY
               ↓
          new mechanism research
```

This is the anti-sprawl loop.

## Immediate implication

The current frozen CAPABILITY_GAP is:

`TRANSFER_STAGING_PRESSURE`.

That matches the unclosed (X) atom from FR-ATOM-001.

So the next mechanism-specific experiment is no longer chosen because transfer
buffers look interesting.

It is chosen because the North-Star system has produced a capability gap for
them.

That is a fundamentally different research policy.

## Next

### FR-XFER-001 — Transfer/Staging Peak Tax

Measure whether a nominally memory-saving migration can create a transient
source + staging + destination peak large enough to cross the memory-pressure
knee.

Compare:

- copy with explicit staging;
- direct copy;
- read-only shared/zero-copy view where semantics permit.

Then register the resulting primitive/effect model and rerun the North-Star
frontier.

If the gap closes, stop transfer research and move to the next measured gap.

## Claim ceiling

**SYNTHETIC_GAP_CLASSIFICATION_AND_RESEARCH_ROUTING_ONLY**
