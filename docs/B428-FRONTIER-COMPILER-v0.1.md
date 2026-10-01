# B428 — Frontier Compiler v0.1

Status: **software instrument + normalized structural examples**. No physical memory benchmark ran.

## 1. Purpose

B426 defined the Live-State Frontier model.

B427 mapped several systems into a common transformation vocabulary.

B428 turns the model into an executable instrument that accepts annotated state intervals and emits:

- logical peak bytes;
- physical peak bytes;
- logical byte-seconds;
- physical byte-seconds;
- peak windows;
- correctness-preserving release candidates;
- potential deduplication savings;
- capacity-cliff ratio.

Implementation:

- src/finite_ram_lab/frontier_compiler.py
- tests/test_frontier_compiler.py

## 2. Input state

Each TraceState has:

- live_start / live_end;
- logical_bytes;
- encoded_bytes;
- replica count;
- metadata bytes per replica;
- fragmentation bytes;
- workspace bytes;
- reuse/access-cost annotations;
- recomputability;
- optional future-sufficient summary.

Physical bytes are modeled as:

encoded_bytes * replicas
+ metadata_bytes_per_replica * replicas
+ fragmentation_bytes
+ workspace_bytes.

Logical bytes are intentionally separate.

## 3. Compiler outputs

For every interval between state-boundary events, the compiler evaluates the active set.

It integrates:

A_logical = integral L(t) dt

and

A_physical = integral M(t) dt

while recording:

P_logical = max_t L(t)

P_physical = max_t M(t).

This gives both peak pressure and time-integrated state exposure.

## 4. Safe-release analysis

The compiler delegates release safety to the B426 fail-closed rules.

A state appears as a release candidate only when:

- it has an explicitly declared smaller future-sufficient summary; or
- it is explicitly declared recomputable.

Unknown recoverability remains RETAIN_OR_MOVE.

The compiler does not infer semantic equivalence from size or naming.

## 5. Physical-overhead accounting

The logical/physical split makes the following visible:

- duplication;
- per-replica metadata;
- fragmentation;
- temporary workspace.

This is useful for separating mechanisms:

- PagedAttention can reduce fragmentation/sharing overhead;
- shared expert arenas can reduce duplicate encoded state;
- graph rewrites such as streaming reductions can reduce logical frontier;
- workspace fusion can reduce temporary physical state.

## 6. Normalized Ozaki structural trace

A deliberately normalized example was frozen in:

- analysis/inputs/B428-NORMALIZED-STRUCTURAL-TRACES-v0.1.json

This is not a real Ozaki benchmark.

Assumptions:

- k=s=8;
- every slice/residue/accumulator state has one equal normalized size unit;
- Ozaki-I model keeps 8 A slices + 8 B slices + one accumulator live for 8 time units;
- Ozaki-II model keeps one accumulator live while one A/B residue pair exists per step;
- compute, traffic, numerical accuracy, and real byte sizes are ignored.

Compiler-equivalent structural results:

| Model | Peak state units | Unit-seconds |
|---|---:|---:|
| materialized Ozaki-I trace | 17 | 136 |
| streaming Ozaki-II trace | 3 | 24 |

The only valid interpretation is:

> Under equal normalized state sizes and the frozen liveness assumptions, streaming residues have a narrower and shorter live-state frontier than fully materialized slices.

This does **not** assert a 5.67x real memory reduction or a real performance advantage.

## 7. Why this matters

The compiler now separates three fundamentally different optimizations.

### A. Logical-frontier rewrite

Examples:

- streamed residues;
- exact online reductions;
- tiled exact algorithms that avoid a global intermediate.

These change what must remain live.

### B. Physical representation

Examples:

- quantization;
- sharing;
- paging;
- deduplication;
- fragmentation reduction.

These change how many physical bytes represent still-required information.

### C. Placement/lifetime

Examples:

- VRAM/RAM/SSD placement;
- mmap;
- managed-memory migration;
- idle unload;
- rematerialization.

These change where and how long physical bytes reside.

A runtime that starts only at C cannot capture gains available at A or B.

## 8. Capacity-cliff hook

B428 exposes:

rho = physical_peak_bytes / effective_capacity_bytes.

This is not yet a performance model. It is a hook for the H426-2 experiment.

Future physical work can correlate rho with:

- page faults;
- reclaim;
- zram/swap traffic;
- GPU page migration;
- reload stalls;
- latency.

The interesting region is expected near rho ~= 1 rather than far below capacity.

## 9. Validation

Isolated authoring validation:

- 7 unit tests PASS;
- 20,000 deterministic randomized interval traces;
- compiler peak outputs matched independent brute-force segment calculations in every randomized case;
- safe-release test preserved fail-closed behavior;
- deduplication arithmetic test PASS;
- capacity-ratio test PASS.

Claim ceiling:

- SOFTWARE_INSTRUMENT;
- NORMALIZED_STRUCTURAL_EXAMPLE.

No physical memory result was produced.

## 10. Next bounce

B429 should stop adding abstractions and perform one controlled **trace translation** from an actual implementation source.

Preferred order:

1. Ozaki Scheme II / GEMMul8 source:
   - identify residue buffer allocation/reuse;
   - identify reconstruction accumulator lifetime;
   - identify materialized intermediates;
   - produce a source-backed TraceState graph.

2. Strata:
   - translate one prefill/decode residency path from public source/release evidence;
   - mark unknown byte sizes as symbolic.

3. FlashAttention:
   - translate one forward-pass tile path.

This will test whether the compiler schema survives real source structure rather than only synthetic traces.
