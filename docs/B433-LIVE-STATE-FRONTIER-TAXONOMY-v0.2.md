# B433 — Live-State Frontier Taxonomy v0.2

Status: **formal taxonomy + source-backed cross-domain model**. No new physical benchmark ran.

## 1. Why v0.2 exists

B426-B431 established a common semantic pattern across numerical precision emulation and exact attention.

B432 added Strata and exposed a physical-model limitation: memory tiers have independent capacities and cannot be represented by one flat physical byte count.

v0.2 therefore separates the problem into two planes.

## 2. Semantic plane

The semantic plane answers:

> What information from the past can still affect a legal future output?

A semantic state records:

- logical state identity;
- future obligation;
- future-sufficient summary, if proven;
- recomputability, if proven;
- owner set;
- semantic live interval.

The fail-closed release rule is:

1. REDUCE when a smaller future-sufficient summary is explicitly known;
2. otherwise REMATERIALIZE when explicit regeneration is known;
3. otherwise RETAIN.

Unknown recoverability never authorizes release.

## 3. Physical plane

The physical plane answers:

> How is required semantic information represented and where is it resident now?

A physical state records:

- representation;
- resident tier;
- backing tier;
- resident bytes;
- replica count;
- phase;
- physical live interval;
- tier capacity.

Important separation:

- one semantic object may have several physical copies;
- several semantic owners may share one immutable physical copy;
- a mapped file may back state without all bytes being resident in RAM.

## 4. Controller order

v0.2 freezes the following control order:

1. SEMANTIC_REDUCTION
2. OWNERSHIP
3. REPRESENTATION
4. TEMPORALIZATION
5. PLACEMENT
6. PHASE_BORROWING
7. LIFETIME

This is an optimization order, not a statement that every stage must modify the program.

The reason is structural.

### 4.1 Semantic reduction first

Do not optimize placement for bytes that need not remain semantically live.

Examples:

- FlashAttention score tiles -> running softmax/output state;
- Ozaki/CRT local product state -> reconstruction state.

### 4.2 Ownership next

Do not encode or place duplicate copies that are not semantically owner-local.

Examples:

- shared immutable expert arena;
- layer-range session carve rather than whole-model session duplication.

### 4.3 Representation

Choose physical encoding after the semantic object and owner set are known.

Examples:

- INT8/Q4 KV;
- tensor compression.

### 4.4 Temporalization

Choose which legal work axis is exposed over time rather than simultaneously.

Examples:

- GEMMul8 m/n/k blocking;
- attention Q/KV tiling;
- hypothetical precision-axis streaming only when correctness is proven.

### 4.5 Placement

Assign the resulting physical state to VRAM, RAM, or another resident tier.

### 4.6 Phase borrowing

Repurpose capacity whose normal owner is inactive in a phase.

Example:

- Strata prompt scratch borrowing expert-cache slots.

### 4.7 Lifetime

Unload state when no near-term phase needs residency.

Example:

- idle model unload.

## 5. Transformation vocabulary

### Semantic reduction

- REDUCE
- REMATERIALIZE

### Ownership

- SHARE
- DEDUP_OWNERSHIP

### Representation

- COMPRESS

### Temporalization

- REORDER
- TEMPORALIZE

### Placement

- MOVE
- PLACE

### Phase borrowing

- BORROW

### Lifetime

- UNLOAD

The vocabulary intentionally stays small.

A real system normally composes several actions.

## 6. Cross-domain mapping

### Ozaki Scheme II

- REDUCE
- REORDER

Local residue/product work is folded into reconstruction state and processed over time.

### FlashAttention

- REDUCE
- REORDER

Score tiles are folded into running (max, sum, output accumulator) state and released.

### PagedAttention

- SHARE
- MOVE

Logical KV information remains, while physical fragmentation and duplicate residency are reduced.

### Checkmate / DTR

- REMATERIALIZE

Intermediate physical state is removed while regeneration provenance remains.

### FlexGen

- COMPRESS
- MOVE

Tensor representation and placement are optimized across memory tiers.

### GEMMul8 memory-saving

- REORDER

Current source-backed memory saving temporalizes m/n/k blocks while keeping the modulus axis fixed within each core call.

### Strata KV streaming

- COMPRESS
- MOVE

KV representation is quantized and only a working subset is resident in VRAM.

### Strata expert residency

- SHARE
- MOVE

One logical expert set is partitioned/shared across GPU cache, RAM complement, and file backing.

### Strata prompt cache lending

- BORROW

A phase temporarily repurposes expert-cache allocation for prompt scratch.

### Strata idle unload

- UNLOAD

Loaded peak may remain unchanged, but wall-time byte-seconds fall.

## 7. The new invariant: ownership is not replica count

This is a crucial distinction.

Suppose semantic state S has owners:

{worker0, worker1, worker2}.

That does not imply three physical copies.

For immutable/shareable state:

owners = 3

may coexist with:

replicas = 1.

For mutable session-local state, sharing may be illegal.

Therefore the planner must record ownership explicitly and decide physical copy count separately.

This is what Strata's host expert sharing and session carve make visible.

## 8. The new invariant: backing is not residency

A 50 GiB mmap file is not automatically 50 GiB of resident RAM.

The file is a backing store.

Actual RAM pressure depends on:

- currently resident page-cache pages;
- pinned/locked mirrors;
- dirty/writeback state;
- reclaim policy;
- cgroup/system pressure.

Therefore:

backing_bytes != resident_bytes.

Finite RAM Lab must observe page-cache residency before charging it to the RAM frontier.

## 9. The new invariant: capacities are a vector

The feasibility condition is not:

sum physical bytes <= one global capacity.

It is:

for every tier j,

M_j(t) <= C_j.

A machine with:

- 8 GiB VRAM free;
- 20 GiB RAM free

does not have one interchangeable 28 GiB memory pool.

Any optimizer that flattens the tiers can generate impossible schedules.

## 10. Objective vector v0.2

The optimization target is now explicitly tiered:

- peak live bytes by tier;
- byte-seconds by tier;
- transfer/traffic bytes;
- compute/recompute work;
- latency;
- numerical or semantic error.

There is no universal scalar optimum.

A controller may select a scalarization only for a bounded decision window.

## 11. Pareto improvement versus exchange

v0.2 keeps the B430 distinction.

### Pareto-improving rewrite

A transformation can dominate the old plan when it reduces memory and does not worsen modeled traffic/compute/latency/error.

Examples may include:

- duplicate elimination;
- fragmentation removal;
- provably dead-state elimination;
- some fusion transformations.

### Memory exchange

A transformation lowers one memory metric while increasing another cost.

Examples:

- smaller tiling;
- offload;
- rematerialization;
- repeated passes;
- idle reload.

The controller must identify which class it is considering.

## 12. Validation

Frozen implementation:

- src/finite_ram_lab/live_state_taxonomy_v02.py
- tests/test_live_state_taxonomy_v02.py
- specs/LIVE-STATE-FRONTIER-TAXONOMY-v0.2.json

Validation during authoring:

- fail-closed semantic release ordering: PASS;
- backing-only state not counted as resident tier bytes: PASS;
- physical replica count kept separate from semantic ownership: PASS;
- all frozen cross-domain exemplar actions mapped to known stages;
- deterministic 20,000 randomized action-order cases preserved the controller order.

Claim ceiling:

FORMAL_TAXONOMY_AND_SOURCE_BACKED_CROSS_DOMAIN_MODEL.

## 13. What is genuinely new in the lab model

The individual techniques are not new:

- sufficient summaries;
- rematerialization;
- communication-avoiding tiling;
- compression;
- paging;
- offload;
- cache borrowing;
- idle unload.

The research contribution being explored is their common decomposition:

> first minimize the information obligation that must survive, then minimize the number and size of physical representations of that obligation, then schedule those representations across independent memory tiers and time.

The model's useful unit is therefore not "tensor" or "allocation".

It is:

**semantic obligation + physical realization**.

## 14. B434 candidate — bounded controller

The next step should turn v0.2 into a small decision controller.

Input:

- semantic states;
- release proofs;
- owner sets;
- representations;
- legal temporalization axes;
- tier capacities;
- transfer/compute/error costs;
- current phase.

Output:

- safe candidate plans;
- per-tier peaks;
- byte-seconds;
- cost vector;
- Pareto frontier.

For tiny problems, solve exactly.

For larger problems, compare a bounded heuristic against exact tiny-window optima.

The controller must never:

- release unproven state;
- merge mutable owners without a sharing proof;
- treat backing bytes as resident;
- violate an individual tier capacity;
- silently scalarize away numerical error.
