# FR-NORTHSTAR-001 — Qualified Task Survival Frontier

Status: **SYNTHETIC NORTH-STAR CONTRACT**

Parent: **FR-COMP-001**

## Zero-base reset

Finite RAM Lab has accumulated strong individual mechanisms:

- representation / quantization;
- duplication removal / sharing;
- allocation / fragmentation control;
- rematerialization;
- page-cache / backing control;
- generic compression;
- demand folding;
- tiering;
- semantic OOM control;
- observation control.

The previous research order asked:

> Which memory mechanism should we study next?

FR-NORTHSTAR-001 replaces that question.

The new question is:

> What is the smallest resident-memory envelope in which useful work can still
> complete under its full task contract?

The mechanisms are no longer research endpoints.

They are compiler primitives.

## North Star

[
oxed{
	ext{Qualified Task Survival Frontier}
}
]

For workload (w), define:

[
M^*(w)
=
min_{pi}
M_{resident}^{peak}(w,pi)
]

subject to:

[
egin{aligned}
quality &ge Q_{min}\
reliability &ge R_{min}\
p99 latency &le L_{max}\
CPU_{extra} &le C_{max}\
IO_{extra} &le I_{max}.
end{aligned}
]

The policy (pi) may compose any qualified primitive.

The primary object is the **frontier**, not one arbitrary scalar score.

A geometric-mean memory-gain summary is reported only as a compact secondary
statistic.

## Why raw RAM reduction is not the North Star

A policy can reduce RAM by:

- recomputing everything;
- moving everything to SSD;
- moving everything to cloud;
- compressing with an extremely slow codec;
- destroying quality;
- missing deadlines.

Those are not legitimate wins.

Therefore:

[
oxed{
	ext{RAM reduction without task survival} = 	ext{failure}
}
]

and:

[
oxed{
	ext{moving cost to another unbounded resource} 
eq 	ext{efficiency}
}
]

## Frozen synthetic contract

The first contract requires:

- p99 latency <= 85 ms;
- quality >= 0.97;
- reliability >= 0.999;
- extra CPU <= 35 abstract units;
- extra IO <= 400 MiB.

These thresholds are synthetic controls.

They are not transferred to real workloads.

## Failure-domain workload suite

Six deliberately different archetypes:

1. **MULTIWORKER_LLM**
   - duplication-heavy;
2. **LONG_CONTEXT**
   - representation/KV-heavy;
3. **SERVING_FRAGMENTED**
   - allocator-fragmentation-heavy;
4. **OUT_OF_CORE**
   - page-cache/backing-path-heavy;
5. **COMPRESSIBLE_CACHE**
   - compressibility-heavy;
6. **REBUILDABLE_PIPELINE**
   - rematerialization-heavy.

The point is not realism.

The point is to challenge the hypothesis that one memory primitive can be the
universal answer.

## Action primitives

The synthetic compiler may choose:

- QUANTIZE;
- SHARE;
- PAGING;
- REMATERIALIZE;
- RECLAIM_PAGECACHE;
- COMPRESS.

Each action reduces one atomic memory term while spending some combination of:

- latency;
- quality;
- reliability;
- CPU;
- IO.

## Single-atom result

The best single action depends on the failure domain:

| workload | best single action |
|---|---|
| MULTIWORKER_LLM | SHARE |
| LONG_CONTEXT | QUANTIZE |
| SERVING_FRAGMENTED | PAGING |
| OUT_OF_CORE | RECLAIM_PAGECACHE |
| COMPRESSIBLE_CACHE | COMPRESS |
| REBUILDABLE_PIPELINE | REMATERIALIZE |

This is the first North-Star result:

[
oxed{
	ext{no single memory primitive dominates all failure domains}
}
]

## Joint result

Geometric-mean minimum-RAM improvement over the baseline contract:

- best single atom: **1.3774x**
- joint composition: **2.2626x**

At a frozen 600 MiB resident-RAM envelope:

- BASELINE: **0 / 6** workloads qualify;
- SINGLE_ATOM: **0 / 6** qualify;
- JOINT: **6 / 6** qualify.

Again, these numbers are synthetic.

The important result is architectural:

> the shortest path to the North Star is a failure-domain-aware composition
> engine, not an endless linear sequence of mechanism-specific research lanes.

## Research-policy inversion

Old policy:

```text
find interesting mechanism
    -> study it deeply
    -> ask later whether it helps the global goal
```

New policy:

```text
measure failure domain
    -> measure distance from Qualified Task Survival Frontier
    -> ask which known primitive or combination closes the gap
    -> only study a new mechanism if the current primitive set cannot close it
```

This does **not** discard earlier work.

It changes its role.

Every previous result becomes:

- an action primitive;
- a constraint;
- a cost model;
- an evidence source;
- or a failure-domain detector.

## North-Star compiler

The proposed system is:

```text
Workload / task contract
        ↓
Observation plane
        ↓
Failure-domain inference
        ↓
Candidate action graph
  ├─ quantize
  ├─ share
  ├─ page
  ├─ recompute
  ├─ offload
  ├─ reclaim
  ├─ compress
  ├─ demand-fold
  └─ future primitives
        ↓
Qualified composition search
        ↓
Causal shadow replay
        ↓
Host-bound calibration
        ↓
Reversible live promotion
```

## The new stopping rule

A mechanism is not prioritized because:

- it is novel;
- it reduces bytes in isolation;
- it has a good benchmark headline;
- it fits the current research sequence.

A mechanism is prioritized only if:

1. a measured workload misses the qualified frontier;
2. existing primitives cannot close that gap under the contract;
3. the new primitive attacks the identified failure domain.

This is the fastest route to the North Star because it prevents research from
expanding sideways indefinitely.

## Immediate next work

### FR-NORTHSTAR-002 — Evidence-backed primitive registry

Convert the current research receipts into machine-readable action records:

- action applicability;
- required observables;
- memory effect;
- latency/CPU/IO effect;
- semantic risk;
- evidence class;
- host binding;
- reversibility;
- failure semantics.

### FR-NORTHSTAR-003 — Causal shadow compiler

Given an observed trace, enumerate only legal actions and predict which
composition would have satisfied the task contract using no future evidence.

### FR-NORTHSTAR-004 — Gap-driven experiment selector

If no existing action qualifies, identify the missing atomic capability and
generate the next experiment specification automatically.

That closes the loop:

[
oxed{
observe
ightarrow
compile
ightarrow
replay
ightarrow
find gap
ightarrow
experiment
ightarrow
update primitive registry
}
]

## Claim ceiling

**SYNTHETIC_NORTH_STAR_CONTRACT_AND_JOINT_POLICY_TOPOLOGY_ONLY**
