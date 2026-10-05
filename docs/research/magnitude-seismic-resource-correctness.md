# Magnitude / Seismic lessons for finite RAM systems

## Thesis

Magnitude's Seismic architecture treats lifetime, storage topology, admission, and resource accounting as correctness concerns rather than after-the-fact optimization metrics. That framing maps directly to finite-ram-lab.

The transferable idea is:

> A computation is not admissible merely because its arithmetic is valid. It must also have a certified resource realization for the execution regime in which it is admitted.

## 1. Separate semantic values from physical storage

Keep the logical computation independent from where a value currently resides.

```text
LogicalValue
  -> representation choice
  -> storage requirement
  -> lifetime interval
  -> placement
  -> physical realization
```

Do not leak SSD/host RAM/GPU RAM/tier-specific movement into the logical algorithm unless the movement itself is semantically observable.

This preserves freedom to change spill, recompute, compression, quantization, and placement policies without changing the computation's meaning.

## 2. Lifetime is part of correctness

For every physical allocation, track at least:

- producer
- first use
- last use
- mutability
- alias constraints
- representation
- size expression
- eviction/recompute eligibility
- persistence requirement

Two buffers may share storage only if their certified lifetimes and alias rules permit it.

This is stronger than heuristic memory reuse: the reuse decision should carry evidence that no live obligation is overwritten.

## 3. Resource certification before execution

Introduce an admission artifact that answers:

```text
Does this plan fit the declared finite-memory regime?
```

Possible fields:

```text
ResourceCertificate
  peak_resident_ram
  peak_gpu_ram
  spill_bytes
  spill_bandwidth_requirement
  scratch_bytes
  persistent_bytes
  liveness_floor
  recompute_cost_bound
  admitted_shapes
  representation_choices
  evidence_digest
```

A run should be admitted only after the selected plan and the certificate agree.

## 4. Preserve semantic topology across memory strategies

Quantization, SSD spill, CPU offload, rematerialization, and chunking should be alternative realizations of the same semantic graph where possible.

```text
Canonical computation
  -> candidate memory plans
      - retain
      - spill
      - quantize
      - recompute
      - stream
  -> feasibility check
  -> cost evaluation
  -> selected plan
```

This prevents memory tactics from becoming independent implementations whose numerical and state semantics drift apart.

## 5. Incomplete is not infeasible

Magnitude's solver distinguishes an interrupted or unproved search from proof that no solution exists. finite-ram-lab should use the same discipline.

```text
Optimal      = globally proved best plan
Feasible     = complete legal plan, no optimality proof
Incomplete   = search coverage unfinished
Infeasible   = no legal plan proved for the declared model
Error        = model/overflow/invariant failure
```

A memory limit that stops search is not evidence of infeasibility.

## 6. Resumable search under memory pressure

Search state itself is finite-memory work. Design retained state so that:

- pending coverage is never silently discarded;
- completed detail may be evicted if a proof-preserving summary remains;
- discarded work can be recomputed;
- a memory stop returns a typed resumable outcome;
- repeating the same insufficient limit is allowed to make no progress rather than inventing a result.

This is directly relevant to finite-RAM optimization loops and low-spec machines.

## 7. Representation choice belongs in the optimization model

Treat representation as a typed decision variable rather than an ad-hoc flag.

Examples:

```text
FP16
BF16
INT8
INT4
AWQ
GPTQ
GGUF variants
BitNet-like representations
```

Each candidate should declare:

- semantic/numerical policy
- conversion cost
- storage cost
- supported operators
- alignment/layout requirements
- device capability requirements
- validation evidence

A representation that saves RAM but violates the admitted numerical policy is not a feasible plan.

## 8. Proposed experiment

Build a tiny finite graph with explicit lifetimes and two memory tiers.

Compare candidate plans:

1. all resident;
2. one tensor spilled to SSD;
3. one tensor quantized;
4. one tensor recomputed;
5. hybrid spill + quantization.

For each plan produce:

- exact peak memory;
- data movement;
- recompute work;
- numerical policy status;
- feasibility result;
- evidence trace.

Then test that changing the physical plan does not change the canonical logical graph.

## Connection to the lab's broader hypothesis

The important new angle is not another eviction heuristic. It is to turn finite memory into a compiler-style proof obligation:

```text
semantic graph
  + device/tier facts
  + representation domain
  + lifetime constraints
  -> certified physical plan
```

That gives the lab a clean place to combine quantization, SSD escape, rematerialization, and scheduling without losing correctness boundaries.
