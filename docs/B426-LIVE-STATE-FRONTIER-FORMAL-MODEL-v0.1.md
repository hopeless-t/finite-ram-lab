# B426 — Live-State Frontier Formal Model v0.1

Status: **software/formal model only**. No physical RAM/VRAM experiment was run in this bounce.

## 1. Research question

The observed techniques in Ozaki Scheme I/II, EmuGEMM, FlashAttention, PagedAttention, Checkmate/DTR, FlexGen, CUDA/ROCm managed memory, and Strata can be described by one question:

> Which state must exist, in what representation, on which memory tier, and for how long, so that future computation remains correct at acceptable cost?

The key shift is from "minimize RAM" to **minimize the live-state frontier under correctness, latency, traffic, compute, and error constraints**.

## 2. State graph

Let a computation be a DAG G=(V,E). Each state v has:

- size s_v(r) under representation r;
- production and future-use times;
- transfer costs between memory tiers;
- recomputation cost;
- numerical/semantic error under lossy representations;
- optional proof of reconstructability;
- optional future-sufficient summary phi_v.

At time t, the live-state frontier is F(t), and memory occupancy is

M(t) = sum_{v in F(t)} s_v.

The primary non-scalar objective is

(P, A, Q, C, T, epsilon)

where:

- P = max_t M(t): peak live bytes;
- A = integral M(t) dt: byte-seconds;
- Q = bytes moved between memory tiers;
- C = compute and recompute work;
- T = latency;
- epsilon = numerical or semantic error.

No single scalar is assumed to dominate this Pareto frontier.

## 3. Future-Sufficient State principle

A transient state x may be released without losing exact future semantics if the retained state contains a smaller representation phi(x) such that every permitted future continuation depends on x only through phi(x).

Informally:

Future(x, R) = Future'(phi(x), R)

for retained state R.

This is the exact-release case.

If no such smaller summary is known, x may still be released when x is explicitly regenerable from retained ancestors at acceptable recomputation cost.

Therefore B426 freezes three conservative modes:

1. REDUCE_AND_RELEASE
   - requires an explicit future-sufficient summary;
   - summary must be smaller than the state.

2. DROP_REMATERIALIZE
   - requires explicit recomputability.

3. RETAIN_OR_MOVE
   - default when neither proof exists.

Unknown recoverability never promotes to release.

This has a useful analogy to sufficient statistics and future-indistinguishability: the memory system should retain the smallest representation needed to distinguish futures that can still affect the result, not necessarily the original intermediate object.

## 4. Rewrite before placement

The optimization hierarchy is:

1. graph rewrite — reduce which states need to exist at all;
2. schedule — reduce overlap between live states;
3. placement — map live states to VRAM/RAM/page-cache/SSD;
4. lifetime — decide when retained state should be unloaded or reconstructed.

This ordering matters.

A placement optimizer cannot recover memory that is structurally required by its input graph. Ozaki II, FlashAttention, fusion, reductions, and rematerialization change the state graph or schedule before placement is solved.

The general problem is therefore:

min over (graph rewrite tau, schedule sigma, placement pi, representation r)

J(tau(G), sigma, pi, r)

subject to capacity and correctness/error constraints.

## 5. Local exchange inequalities

Let mu_j(t) be the marginal carrying cost ("shadow price") of one byte on tier j.

### 5.1 Future-sufficient reduction

If state x of size s_x can be replaced by an exact summary of size s_phi, then over [t0,t1] reduction is locally favorable when

integral_{t0}^{t1} mu(t) * (s_x - s_phi) dt > transform_cost + added_traffic_cost.

This explains why the same transformation may be worthless when memory is plentiful but valuable near a capacity cliff.

### 5.2 Rematerialization

A recomputable state can be dropped when

integral mu(t) * s_x dt > P(reuse) * recompute_cost + release/rebuild overhead.

This is the local form of the checkpoint/rematerialization trade-off used by systems such as Checkmate and DTR.

### 5.3 Fast-tier residency

For state i, a simple bounded-horizon value density is

Theta_i =
  expected_accesses_i
  * max(0, slow_access_cost_i - fast_access_cost_i)
  / size_i.

This is the expected access-cost savings per fast-tier byte.

B426 includes a tiny exact enumerator and a value-density greedy heuristic for this placement subproblem.

## 6. Mapping existing systems into the model

### Ozaki Scheme I

- graph form: multiple precision slices remain materialized;
- effect: large live-state overlap;
- dominant costs: P, A, and growing GEMM count;
- research role: materialize-first baseline.

### Ozaki Scheme II

- graph rewrite: precision is streamed through residues;
- each residue can be consumed, incorporated into reconstruction state, then released;
- effect: turns spatial live state into temporal work;
- research role: canonical REDUCE_AND_RELEASE example.

Reference:
https://arxiv.org/abs/2504.08009

### EmuGEMM

- graph/kernel rewrite: fuse work that otherwise materializes intermediates in global memory;
- primary effect: Q decreases; P/A can also decrease depending on implementation.

Reference:
https://arxiv.org/abs/2606.25453

### FlashAttention

- schedule + graph rewrite: tiled attention and online normalization avoid materializing the full attention matrix;
- primary effect: HBM<->SRAM traffic reduction and a smaller materialized frontier.

Reference:
https://arxiv.org/abs/2205.14135

### PagedAttention

- representation/allocator rewrite: page KV state;
- sharing removes duplicate state;
- paging reduces fragmentation slack;
- primary effect: physical live bytes approach logical live bytes more closely.

Reference:
https://arxiv.org/abs/2309.06180

### Checkmate / Dynamic Tensor Rematerialization

- state is dropped while a regeneration path is retained;
- primary exchange: A/P decrease in return for increased C.

References:
https://arxiv.org/abs/1910.02653
https://arxiv.org/abs/2006.09616

### FlexGen

- solves multi-tier tensor placement across GPU/CPU/disk and combines placement with compression;
- primary role: explicit optimization of placement after the state graph is known.

Reference:
https://arxiv.org/abs/2303.06865

### CUDA Unified Memory / ROCm HMM

- keep one logical addressable state while physical pages migrate between tiers;
- primary role: reactive MOVE policy and oversubscription baseline.

References:
https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html
https://rocm.docs.amd.com/en/docs-6.1.5/conceptual/gpu-memory.html

### Strata

Observed recent design changes map naturally to:

- KV quantization -> representation;
- mmap experts -> deferred residency;
- resident experts -> tier placement;
- per-GPU session state -> ownership partition;
- shared expert arena -> deduplication/sharing;
- cache lending -> phase-local borrowing;
- idle unload -> lifetime control.

Strata is therefore useful as an application-level case study for the full model rather than only one technique.

## 7. Connection to peak-memory scheduling theory

Peak-memory scheduling corresponds to weighted one-shot pebbling on computation graphs. Recent work shows this problem is strongly NP-complete even on restricted graph classes.

Reference:
https://arxiv.org/abs/2312.13526

This matters operationally: a globally optimal scheduler is not the default expectation.

Finite RAM Lab therefore keeps a bounded-horizon strategy:

observe -> solve a small local problem -> execute -> receipt -> re-observe.

This resembles model-predictive control and matches the lab's existing multi-bounce workflow.

## 8. New decomposition: six legal state transformations

B426 currently recognizes six orthogonal moves:

1. COMPRESS
   - change representation; may add epsilon.

2. REDUCE
   - replace a state by a future-sufficient smaller state.

3. REMATERIALIZE
   - release state while preserving regeneration provenance.

4. MOVE
   - retain full state but place it on a slower tier.

5. SHARE
   - merge physically duplicate equivalent state.

6. REORDER
   - change schedule to shorten simultaneous liveness.

Many real systems use several at once.

## 9. New research hypothesis: rewrite-before-placement dominance

Hypothesis H426-1:

> Under a fixed correctness constraint, systems that can safely reduce the logical live-state frontier before placement will dominate placement-only systems in at least one of P or A, unless rewrite overhead offsets the saved carrying cost.

This is deliberately not stated as a universal performance theorem because Q, C, T, and epsilon can move in the opposite direction.

## 10. New research hypothesis: capacity-cliff shadow price

Let W be live working set and C_eff effective usable fast memory.

rho = W / C_eff.

Hypothesis H426-2:

> The marginal value of one freed byte is low for rho << 1 but rises sharply near rho ~= 1 because eviction, page migration, reclaim, swap, or reload costs become active.

A future physical experiment should estimate the empirical curve

mu(W) ~= - d(latency) / d(free_bytes)

around the knee rather than report only average RAM usage.

## 11. New research hypothesis: phase-dependent state temperature

Reuse hazard is time-dependent:

lambda_i = lambda_i(t).

Hypothesis H426-3:

> Phase-aware placement can outperform a globally fixed "hot set" because state value density changes between prefill, decode, idle, checkpoint, and other phases.

This directly motivates testing Strata-style cache lending and idle unload against static residency.

## 12. Software validation in this bounce

The reference implementation is:

- src/finite_ram_lab/live_state_frontier.py
- tests/test_live_state_frontier.py
- specs/TX-LIVE-STATE-FRONTIER-v0.1.json

Isolated authoring validation:

- 11 unit tests PASS;
- 20,000 deterministic randomized cases: greedy placement never exceeded byte capacity;
- 2,000 deterministic small cases: exact enumerator was never worse than the greedy heuristic.

These tests validate implementation invariants only. They are not physical memory-performance evidence.

## 13. Next bounded research bounce

B427 should turn the formal model into a common comparison input for four initial exemplars:

- Ozaki Scheme I;
- Ozaki Scheme II;
- FlashAttention;
- Strata expert residency.

For each exemplar, encode:

- logical state graph;
- live intervals;
- state sizes;
- release proof type;
- traffic edges;
- recompute/reduction costs;
- memory tiers.

Then compute symbolic or measured deltas in:

(P, A, Q, C, T, epsilon).

Do not combine this with the pending B425 physical ambient canary. The two tracks remain scientifically independent.
