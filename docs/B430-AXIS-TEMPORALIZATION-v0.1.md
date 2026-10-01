# B430 — Axis Temporalization v0.1

Status: **normalized optimization model only**. No physical GPU/CPU benchmark ran.

## 1. New question

B429 showed that current GEMMul8 memory-saving mode keeps NUM_MODULI fixed while searching smaller m/n/k blocks.

This motivates a more general finite-memory question:

> Given several independent computation axes, which axes should be temporalized under a memory bound?

For a GEMM-like workload use:

- m, n, k: matrix axes;
- p: precision/modulus axis.

A block plan is b = (b_m, b_n, b_k, b_p).

The normalized invocation multiplicity is:

N_calls(b)
=
ceil(m/b_m)
* ceil(n/b_n)
* ceil(k/b_k)
* ceil(p/b_p).

A smaller block can reduce simultaneous state while increasing the number of invocations and usually traffic/overhead.

## 2. Fail-closed legality

The p axis is special.

Matrix blocking is a known legal transformation for GEMM accumulation.

Precision/modulus blocking is not assumed legal automatically.

B430 therefore freezes:

- if b_p = p, no extra proof is required;
- if b_p < p, precision_streaming_proven must be true;
- otherwise the plan is rejected before optimization.

This preserves the B426 rule that memory reduction may not invent recoverability.

For GEMMul8 today, B429 leaves precision_streaming_proven = false at the implementation level.

## 3. Normalized workspace model

B430 uses a deliberately synthetic workspace geometry:

W(b) =
A_low(b)
+ B_low(b)
+ active_product(b)
+ reduced_product(b)
+ carried_summary(b)
+ fixed.

If the p axis is not temporalized, all p reduced-product planes are represented in the model.

If p is temporalized under an explicit proof, only the local p block plus a compact carried summary is represented.

This is not the GEMMul8 workspace formula. The exact current INT8-real GEMMul8 formula remains in B429.

The purpose here is to study scheduling geometry.

## 4. Exact-search example

Frozen in:

- analysis/inputs/B430-AXIS-TEMPORALIZATION-NORMALIZED-v0.1.json

Synthetic extents:

- m=n=k=16
- p=8
- memory limit=100 normalized units.

### m/n/k-only legal set

Precision streaming not proven.

Exact search best plan:

- bm=1
- bn=3
- bk=2
- bp=8
- workspace=100
- normalized invocations=768.

### m/n/k/p legal set

Assume, only for this synthetic experiment, that an exact future-sufficient precision summary has been proven.

Exact search best plan:

- bm=2
- bn=2
- bk=16
- bp=1
- workspace=100
- normalized invocations=512.

Interpretation:

Adding another legally temporalizable axis enlarged the feasible scheduling space and reduced the normalized call-count objective in this constructed case.

It does not show that modulus streaming is faster in GEMMul8.

## 5. Connection to communication lower bounds

This model connects directly to classic communication-avoiding linear algebra.

Hong-Kung-style matrix multiplication lower bounds, and later extensions, show that when a conventional matrix multiply operates with a bounded fast memory M, required communication has a lower-bound scaling of approximately:

arithmetic_work / sqrt(M).

Reference:

- Ballard, Demmel, Holtz, Schwartz, Minimizing Communication in Linear Algebra
- arXiv:0905.2485

So ordinary blocking is an exchange transformation:

memory down
<-> communication / invocation overhead up.

It is not free.

FlashAttention makes the same principle explicit for attention by designing tiles around SRAM/HBM movement, and later I/O-complexity work establishes matching bounds over broad cache-size regimes.

References:

- arXiv:2205.14135
- arXiv:2402.07443

## 6. Two classes of memory optimization

The Live-State Frontier model now benefits from a new distinction.

### A. Pareto-improving frontier rewrites

These remove avoidable state or movement without necessarily paying another modeled axis.

Examples can include, when applicable:

- eliminating duplicate immutable state;
- removing fragmentation;
- kernel fusion that avoids redundant materialization;
- deleting provably dead state.

Potential signature:

- P decreases;
- Q/C/T/epsilon do not increase.

These can dominate the old implementation.

### B. Memory-exchange transformations

These deliberately trade memory for another resource.

Examples:

- smaller tiling;
- offload;
- rematerialization;
- extra precision/residue passes;
- recomputation.

Signature:

- P decreases;
- at least one of Q, C, T, epsilon cost increases.

This distinction prevents the lab from treating every memory-saving method as equivalent.

## 7. Axis choice is now part of the optimizer

The prior B426 control variables were:

- representation;
- graph rewrite;
- scheduling;
- placement;
- lifetime.

B430 refines scheduling into:

- which axis is temporalized;
- how much of that axis is simultaneously resident.

This creates a block vector rather than one generic chunk size.

Examples:

- GEMMul8 memory saving: m/n/k;
- conceptual Ozaki-II streaming: p/modulus;
- FlashAttention: sequence/tile axes;
- Strata: layer/expert/request phase and time;
- out-of-core linear algebra: matrix dimensions + storage tier.

## 8. Geometric interpretation

A computation has a multidimensional state volume.

A schedule exposes only a cross-section of that volume at one time.

Reducing memory is therefore equivalent to selecting a narrower moving cross-section.

But a narrower section must sweep the volume more times.

This gives the intuitive duality:

> frontier width versus sweep count

or, in systems terms:

> resident state versus communication/replay.

The communication lower bound tells us that some of this trade cannot be optimized away by implementation cleverness alone.

## 9. New hypothesis H430

**H430 — Axis-choice hypothesis**

> Under a fixed correctness constraint and memory bound, the best finite-memory schedule depends not only on block size but on which semantically independent axes are allowed to be temporalized.

Corollary for research design:

A system exposing only one blocking dimension may be suboptimal even when its block-size search is perfect.

That is not a claim about current GEMMul8 performance; it is a general search-space hypothesis.

## 10. Software artifacts

Frozen on branch:

- research/axis-temporalization-b430

Files:

- src/finite_ram_lab/axis_temporalization.py
- tests/test_axis_temporalization.py
- analysis/inputs/B430-AXIS-TEMPORALIZATION-NORMALIZED-v0.1.json
- docs/B430-AXIS-TEMPORALIZATION-v0.1.md

The implementation:

- enumerates compact block candidates;
- rejects precision-axis temporalization without proof;
- enforces a memory limit;
- minimizes normalized invocation count;
- classifies a memory transformation as:
  - PARETO_IMPROVEMENT;
  - MEMORY_EXCHANGE;
  - NO_CHANGE;
  - MIXED_OR_NONMEMORY.

Isolated validation during authoring:

- fail-closed precision proof gate PASS;
- fixed normalized examples PASS;
- deterministic 10,000-case randomized feasible-plan sweep PASS.

Claim ceiling remains NORMALIZED_OPTIMIZATION_MODEL_ONLY.

## 11. Next bounce B431

The next step should test the theory against another real implementation, not add another synthetic abstraction.

Best candidate: FlashAttention.

Questions:

1. Which exact intermediate state is avoided?
2. Which state is the future-sufficient running summary?
3. Which axis is tiled?
4. What does the source-backed tile frontier look like?
5. Does the B428 compiler represent it without schema changes?

If yes, then the same model has survived both:

- an Ozaki-II implementation;
- an unrelated exact attention implementation.

That would be meaningful cross-domain evidence for the Live-State Frontier model.
