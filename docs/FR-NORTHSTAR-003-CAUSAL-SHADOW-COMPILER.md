# FR-NORTHSTAR-003 — Causal Shadow Compiler

Status: **SYNTHETIC CAUSAL SHADOW COMPILER**

Parent: **FR-NORTHSTAR-002**

## Purpose

FR-NORTHSTAR-001 defined the qualified survival frontier.

FR-NORTHSTAR-002 turned prior research into evidence-backed primitives.

FR-NORTHSTAR-003 connects them without executing anything.

The compiler consumes:

- a task/workload state;
- a causal evidence stream;
- the primitive registry;
- synthetic effect models for primitives that have one.

It outputs the best **shadow-only** qualified action composition that could have
been chosen with information available at that moment.

## Causal evidence rule

The compiler reuses FR-GFX-007's rule:

[
s^*(t)
=
max{s_i:s_ile t}.
]

Future samples are forbidden.

Stale and missing evidence fail closed.

This matters because the North Star is easy to cheat in offline replay.

## Registered does not mean schedulable

The primitive registry contains more actions than the shadow compiler can
currently model quantitatively.

For FR-NORTHSTAR-003, only these have synthetic effect models:

- QUANTIZE_STATE;
- SHARE_IMMUTABLE_MMAP;
- PAGED_ALLOCATE;
- REMATERIALIZE_STATE;
- RECLAIM_CLEAN_FILE_CACHE;
- COMPRESS_STATE.

A registered primitive without an effect model is marked:

`NOT_SCHEDULABLE`.

It is not silently assumed beneficial.

## Adversarial future-leakage fixture

At target time (t=1000), the MULTIWORKER_LLM workload has fresh past evidence
at (t=950), but that evidence does **not** prove duplication sharing is
applicable.

At (t=1010), a future evidence record appears that would make
`SHARE_IMMUTABLE_MMAP` eligible.

A nearest-neighbor offline join can incorrectly use the future record.

The causal compiler cannot.

## Frozen result

At the 600 MiB North-Star budget:

- causal compiler: **5 / 6** workloads qualify;
- leaky nearest-neighbor compiler: **6 / 6** qualify.

The leaky compiler looks better.

It is wrong.

For MULTIWORKER_LLM:

- causal minimum qualified RAM: **681.5 MiB**;
- leaky future-informed RAM: **369.9 MiB**.

The apparent gain exists only because the leaky replay learned a fact before it
was available.

Therefore:

[
oxed{
	ext{better offline frontier}

otRightarrow
	ext{better controller}
}
]

unless evidence causality is preserved.

## Stale evidence

A later synthetic snapshot is intentionally placed outside the evidence-age
window.

The compiler returns:

`INSUFFICIENT_EVIDENCE`

and schedules no mutating action.

This is a deliberate fail-closed state.

## Execution boundary

The compiler never executes an action.

Frozen governance:

- live actions executed: 0;
- future evidence: forbidden;
- stale evidence: fail closed;
- missing evidence: fail closed;
- unknown effect model: not schedulable.

This keeps:

[
	ext{research inference}

eq
	ext{execution authority}.
]

## Why this is the shortest path to the North Star

We no longer need to wait for a perfect universal controller before learning.

Every new workload trace can now be used to ask:

1. what failure domains were observable at each instant?
2. which existing primitives were legally applicable?
3. which qualified combination would have minimized resident RAM?
4. what blocked the frontier if none qualified?

That last question feeds directly into the next lane.

## Next

### FR-NORTHSTAR-004 — Gap-driven Experiment Selector

When the compiler cannot reach the target frontier, classify the blocker as:

- **EVIDENCE_GAP**
  - the capability may exist but required evidence is missing;
- **MODEL_GAP**
  - a primitive exists but has no qualified effect model;
- **CAPABILITY_GAP**
  - no registered primitive attacks the binding failure domain;
- **CONTRACT_GAP**
  - every known action violates latency/quality/reliability/CPU/IO constraints.

Only CAPABILITY_GAP should normally spawn a new mechanism research lane.

This is the main anti-sprawl rule.

## Claim ceiling

**SYNTHETIC_CAUSAL_SHADOW_COMPILER_ONLY**
