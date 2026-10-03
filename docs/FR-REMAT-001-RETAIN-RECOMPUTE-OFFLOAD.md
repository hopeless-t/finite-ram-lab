# FR-REMAT-001 — Retain / Recompute / Offload Planner

Status: **SOURCE-GROUNDED SYNTHETIC REMATERIALIZATION PLANNER**

Parent: **FR-ALLOC-001**

## Why this atom exists

After reducing:

- semantic obligation;
- representation density;
- duplication;
- residency;
- fragmentation;

there is a more radical question:

> Why store this state at all?

Activation checkpointing answers this by discarding selected forward
intermediates and recreating them later.

PyTorch explicitly describes activation checkpointing as a memory-vs-compute
trade.

Selective Activation Checkpointing and memory-budget tooling make the choice
more granular: cheap operations are attractive recompute candidates while
expensive operations are worth saving.

Checkmate formalizes tensor rematerialization as an optimization problem rather
than a fixed heuristic.

Dynamic Tensor Rematerialization provides a runtime-relative that makes
eviction/recomputation decisions dynamically.

Recent PyTorch/TorchTitan offload work adds a third choice:

- **retain** spends fast memory;
- **recompute** spends compute;
- **offload** spends slower-tier capacity and transfer bandwidth.

This maps directly onto Finite RAM Lab.

## Frozen resource model

Fast-tier budget:

**256 MiB**

Slow-tier budget:

**256 MiB**

Seven synthetic semantic objects total:

**648 MiB**

So KEEP_ALL is infeasible.

The objects deliberately vary in:

- byte size;
- recomputation cost;
- future reuse count;
- offload cost;
- whether exact reconstruction is legal.

One object, `EXTERNAL_RESULT_G`, is non-rebuildable.

The planner must never silently recompute it.

## Objective

The synthetic objective is:

[
J =
E[	ext{overhead}]
+
0.15cdot	ext{tail proxy}
+
0.002cdot	ext{transfer MiB}.
]

These coefficients are synthetic controls.

The purpose is to validate planner topology, not claim real hardware timings.

## Baseline 1 — drop largest and recompute

A byte-greedy policy drops the largest rebuildable objects until the fast
budget fits.

Frozen result:

- fast residency: **216 MiB**
- mean overhead: **98 ms**
- objective: **116.375**

This saves memory aggressively but recomputes expensive attention/matmul state.

## Baseline 2 — cheap recompute first

Rank rebuildable objects by expected recompute cost per MiB.

Frozen result:

- fast residency: **232 MiB**
- mean overhead: **51 ms**
- objective: **60.5625**

This is much better than dropping the largest objects.

So:

[
oxed{
	ext{bytes freed}

eq
	ext{value of a rematerialization action}
}
]

## Exhaustive mixed planner

The optimal frozen mixed policy is:

| object | action |
|---|---|
| POINTWISE_A | RECOMPUTE |
| MATMUL_B | OFFLOAD |
| ATTN_C | KEEP |
| NORM_D | RECOMPUTE |
| EMBED_E | RECOMPUTE |
| ROUTER_F | KEEP |
| EXTERNAL_RESULT_G | OFFLOAD |

Result:

- fast residency: **240 MiB**
- slow residency: **200 MiB**
- mean overhead: **40 ms**
- tail proxy: **65.95 ms**
- transfer: **656 MiB**
- objective: **51.2045**

Compared with cheap-recompute-first:

[
60.5625ightarrow51.2045
]

or about **15.45% lower synthetic objective**.

The important result is not the exact number.

It is that the optimum uses all three actions at once.

## Rebuildability is a semantic property

Rematerialization is only valid if state can be reconstructed faithfully enough
for the task.

Examples of dangerous candidates:

- nondeterministic side effects;
- external API responses that may change;
- secrets or one-time credentials;
- state whose source has disappeared;
- stochastic operations whose exact replay state was not retained.

Therefore every semantic object needs something like:

`rebuildable: true/false`

and potentially:

- reconstruction source;
- deterministic replay identity;
- quality loss;
- rebuild deadline;
- dependency closure.

A memory controller must fail closed when reconstruction validity is unknown.

## New memory value density

A first useful heuristic is:

[
V_i
approx
rac{
n_i c_i + lambdacdot tail_i
}{
m_i
}
]

where:

- (m_i) = resident bytes;
- (c_i) = rebuild cost;
- (n_i) = expected future uses.

High (V_i) state is expensive to reconstruct per byte and should tend to stay
resident.

Low (V_i) state is a natural rematerialization candidate.

This is only a heuristic because dependencies and shared subgraphs can make the
true problem non-local.

## Interaction with earlier atoms

The decision is now:

[
	ext{semantic object}
ightarrow
egin{cases}
	ext{KEEP} \
	ext{QUANTIZE + KEEP} \
	ext{SHARE} \
	ext{OFFLOAD} \
	ext{RECOMPUTE} \
	ext{DROP}
end{cases}
]

subject to:

- correctness / quality;
- fast-memory budget;
- slow-tier budget;
- transfer bandwidth;
- compute budget;
- deadlines;
- tail reliability.

This is no longer a conventional cache policy.

It is a **state survival compiler**.

## Next

### FR-REMAT-002

Add dependency graphs.

The cost of rebuilding one object should depend on which ancestors remain
resident.

Compare:

- local value-density heuristic;
- greedy checkpointing;
- dynamic rematerialization;
- exact small-graph optimizer.

### FR-ATOM-002

Combine the current atoms into one joint policy space:

[
Q	imes R	imes D	imes F	imes G	imes W.
]

The research question becomes:

> Which atom should be attacked first under the current failure domain?

## Claim ceiling

**SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY**
