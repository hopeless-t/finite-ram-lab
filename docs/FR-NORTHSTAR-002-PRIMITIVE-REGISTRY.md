# FR-NORTHSTAR-002 — Evidence-backed Primitive Registry

Status: **MACHINE-READABLE RESEARCH ACTION REGISTRY**

Parent: **FR-NORTHSTAR-001**

## Why this exists

The zero-base reset changed the role of prior research.

A PR is no longer merely a result to remember.

If it can affect the North Star, it must become a machine-readable primitive
with explicit:

- applicability;
- evidence class;
- resource costs;
- reversibility;
- mutation scope;
- fail-closed conditions;
- claim ceiling.

This lets the future North-Star compiler reason over the existing research
portfolio instead of depending on human memory or mechanism-specific code.

## Evidence hierarchy

The registry currently distinguishes:

1. `SOURCE_GROUNDED`
2. `SYNTHETIC`
3. `HOSTED_PHYSICAL`
4. `HOST_BOUND_PHYSICAL`

The hierarchy is intentionally conservative.

A hosted GitHub runner result may prove a physical mechanism exists.

It does **not** prove the mechanism is safe or beneficial on the development
machine.

Therefore:

[
oxed{
	ext{HOSTED_PHYSICAL}

eq
	ext{live promotion authority}
}
]

## Current action primitives

The first registry contains:

- QUANTIZE_STATE;
- SHARE_IMMUTABLE_MMAP;
- PAGED_ALLOCATE;
- PREFIX_SHARE;
- REMATERIALIZE_STATE;
- OFFLOAD_STATE;
- RECLAIM_CLEAN_FILE_CACHE;
- COMPRESS_STATE;
- DEMAND_FOLD;
- SEMANTIC_TIER.

These are not all equally mature.

That difference is part of the data.

## Support primitives

Some research results are not memory actions themselves but are necessary for a
safe compiler:

- ADAPTIVE_OBSERVATION;
- OBSERVER_ABA_QUALIFICATION;
- READONLY_PROCFS_COLLECTOR;
- CAUSAL_ASOF_JOIN.

They become support primitives rather than being lost in a graphics-only
research branch.

## Fail-closed semantics

Every mutating primitive carries explicit conditions that make it illegal.

Examples:

### QUANTIZE_STATE

Fail closed when:

- quality impact is unknown;
- the kernel does not support the representation;
- state type is unknown.

### SHARE_IMMUTABLE_MMAP

Fail closed when:

- mutability is unknown;
- private writes are required;
- backing identity is not proven.

### REMATERIALIZE_STATE

Fail closed when:

- rebuildability is unknown;
- state depends on nondeterministic side effects;
- the rebuild deadline is unknown.

### OFFLOAD_STATE

Fail closed when:

- restore deadline is unknown;
- transfer budget is unknown;
- delivery is unknown.

## No live actions yet

The most important frozen result in this PR is:

[
oxed{
	ext{live promotion candidates}=0
}
]

This is deliberate.

The registry does not confuse:

- mechanism evidence;
- applicability;
- host calibration;
- execution authority.

Before a primitive can become a live candidate it needs host-bound physical
evidence and its own promotion contract.

## Example queries

A compiler can now ask:

> Which reversible actions address duplication and have at least hosted physical
> evidence?

Result:

`SHARE_IMMUTABLE_MMAP`.

For page-cache pressure:

`RECLAIM_CLEAN_FILE_CACHE`.

For compressible state:

`COMPRESS_STATE`.

Quantization remains synthetic in the current lab evidence hierarchy, so a
`HOSTED_PHYSICAL` query does not return it.

That distinction is exactly what the registry is for.

## Research architecture after the reset

```text
evidence receipts
      ↓
primitive registry
      ↓
failure-domain observation
      ↓
legal-action filtering
      ↓
qualified composition search
      ↓
causal shadow replay
      ↓
host-bound qualification
      ↓
separate execution authority
```

## Next

### FR-NORTHSTAR-003 — Causal Shadow Compiler

Input:

- task contract;
- failure-domain evidence;
- causal trace;
- primitive registry.

Output:

- legal candidate compositions;
- rejected candidates with reasons;
- predicted resource envelope;
- evidence completeness;
- qualified / unqualified decision.

The compiler must not treat missing evidence as zero and must not use future
trace values.

### FR-NORTHSTAR-004 — Gap-driven Experiment Selector

If no legal composition qualifies, identify:

- which task-contract constraint is binding;
- which atomic failure domain is responsible;
- whether the gap is missing evidence or missing capability.

Only then should the lab create another mechanism-specific experiment.

## Claim ceiling

**REGISTRY_STRUCTURE_AND_EVIDENCE_ROUTING_ONLY**
