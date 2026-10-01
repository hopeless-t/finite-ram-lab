# B429 — GEMMul8 Source-Backed Live-State Trace v0.1

Status: **source-backed static model**. No GPU benchmark or physical VRAM measurement was executed.

Upstream source pin:

- repository: RIKEN-RCCS/GEMMul8
- commit: 603b52363715796a0af5e4aa1ed8d386349b4251

## 1. Purpose

B428 used a deliberately synthetic Ozaki-II trace in which only one residue pair was live at a time.

B429 asks a stricter question:

> Does the current GEMMul8 implementation actually have that liveness geometry?

For the inspected real INT8 GEMM path, the answer is **no**.

The algorithmic possibility of streaming residues and the current implementation's workspace policy must be treated separately.

## 2. Source-backed execution stages

The inspected `oz2_core` path is structurally:

1. scale/quantize A and B into `A_lo` / `B_lo`;
2. compute high product planes `C_hi`;
3. reduce those products to modulus/group residues;
4. retain reduced product state;
5. perform final CRT reduction and undo scaling;
6. update output C.

The public timing interface mirrors this as:

- scaling/quantization;
- low-precision matrix multiplication;
- product re-quantization;
- final CRT reduction / undo scaling.

## 3. A/B are not one-pair streamed in current INT8 real GEMM

`common::table::num_mat_constexpr` returns `NUM_MODULI` for the INT8 backend.

`core::workSize` allocates:

`sizeof(LowT) * sizeA * num_A_lo`

and

`sizeof(LowT) * sizeB * num_B_lo`.

For INT8 real fast mode without skip-scaling planes:

- LowT = int8_t;
- num_A_lo = NUM_MODULI;
- num_B_lo = NUM_MODULI.

`oz2_core` then establishes `A_lo` and `B_lo` over those full low-plane regions before entering the product loop.

Therefore the current implementation materializes all input low/residue planes needed by the call.

B428's one-residue-pair peak model is **not** a valid source-backed model of current GEMMul8.

## 4. Product state is hierarchical, not simply fully materialized

The output side is more sophisticated.

### Non-grouped CRT

For large `sizeC`, completed high products are converted to `C_mid`.

For INT8 real:

- MidT = int8_t;
- HiT = int32_t.

The product workspace layout reserves prior `C_mid` residue planes plus high-product storage for the active modulus batch.

The final modulus can remain in high form as `tail.ptr0`, avoiding one final C_mid write before final CRT.

### Grouped CRT

When:

`sizeC <= 8192 * 8192`

GEMMul8 uses grouped CRT.

`crt_group_end` groups at most four moduli while requiring their product to fit in uint32.

For INT8 real moduli 0..19, this produces groups of four with a shorter final tail when NUM_MODULI is not divisible by four.

A completed group is reduced into one uint32 group plane.

Thus the implementation performs a hierarchical reduction:

`multiple C_hi modulus products -> one uint32 CRT-group state -> final CRT`.

The final group can be fused into final reconstruction rather than stored as another group plane.

This is already a REDUCE transformation in the B426 vocabulary.

## 5. Source-backed INT8 real workspace formula

For GEMM:

- `m_pad = pad256(m)`
- `n_pad = pad256(n)`
- `k_pad = pad256(k)`
- `sizeA = k_pad * m_pad`
- `sizeB = k_pad * n`
- `sizeC = m_pad * n`

For fast mode, no skip-scaling planes:

`WorkA = 255 + sizeA * NUM_MODULI + 2*m_pad`

`WorkB = 255 + sizeB * NUM_MODULI + 2*n_pad`.

The exact C-workspace calculation depends on grouped/non-grouped CRT and includes a 32 MiB BLAS workspace floor.

The executable mirror is frozen in:

- src/finite_ram_lab/gemmul8_source_trace.py

## 6. Concrete static example

Input:

- real INT8 GEMM;
- m=n=k=4096;
- NUM_MODULI=8;
- fast mode;
- no skip-scaling;
- current source pin.

Because `sizeC = 4096^2 <= 8192^2`, grouped CRT is selected.

INT8 real groups:

- [0,4)
- [4,8)

Source-derived workspace requirement:

- WorkA = 134,226,175 bytes ~= 128.008 MiB
- WorkB = 134,226,175 bytes ~= 128.008 MiB
- WorkC = 402,653,439 bytes ~= 384.000 MiB
- total = 671,105,789 bytes ~= 640.016 MiB

This is a calculation from the pinned workspace source, **not a physical VRAM measurement**.

It excludes memory outside the GEMMul8 workspace contract such as the caller's original A/B/C allocations and runtime/driver allocations.

## 7. Memory-saving mode reveals a new optimization axis

`gemm_core` checks:

`full_worksize <= max_worksize`.

If the call does not fit and memory saving is enabled, it calls `find_block_size_gemm`.

That search varies:

- m block size;
- n block size;
- k block size;

and repeatedly evaluates the same `workSize(..., NUM_MODULI, ...)`.

`NUM_MODULI` remains fixed.

Execution then loops over:

- i in m blocks;
- j in n blocks;
- p in k blocks;

and calls the same Ozaki-II core on each smaller block.

Therefore current memory-saving mode primarily performs:

**matrix-axis temporalization**,

not:

**modulus-axis temporalization**.

This is a new distinction not explicit in B428.

## 8. Axis Temporalization model

Let a computation have separable work axes:

`D = (m, n, k, p, ...)`

where p denotes precision/modulus work.

Choose block vector:

`b = (b_m, b_n, b_k, b_p, ...)`.

A generic finite-memory scheduler solves:

minimize execution cost / call count / traffic

subject to:

`W(b) <= C_effective`.

Approximate invocation multiplicity is:

`N_calls ~= ceil(m/b_m) * ceil(n/b_n) * ceil(k/b_k) * ceil(p/b_p)`

when the axes can legally be blocked independently.

Current GEMMul8 memory-saving exposes:

- b_m
- b_n
- b_k

while effectively fixing:

- b_p = p = NUM_MODULI

for the A/B low-plane allocation of each Ozaki-II core call.

This identifies an unexplored design dimension:

> Can some precision/modulus state also be safely temporalized without increasing accumulator/CRT cost enough to erase the memory gain?

This is a research question, not a claim that GEMMul8 should do so.

## 9. Why fully streaming moduli is not automatically better

The source shows why a simplistic "one modulus at a time" rewrite is not free.

Current grouped CRT obtains benefits from:

- batched low-precision matrix multiplication;
- group reduction into uint32;
- a fused last high-product tail;
- reusable BLAS workspace;
- architecture-dependent batching;
- FP8 plans where one modulus may require multiple product planes.

A modulus-streamed variant could increase:

- kernel launch count;
- scaling/quantization repetition;
- memory traffic;
- CRT accumulator width/work;
- loss of batched GEMM efficiency.

So the correct optimization objective remains the B426 Pareto vector:

`(P, A, Q, C, T, epsilon)`

rather than peak memory alone.

## 10. Correction to the synthetic B428 picture

Retain:

- Ozaki Scheme II admits a temporal precision decomposition at the algorithm level.
- streamed residue processing remains a legitimate design point.

Correct:

- current GEMMul8 is not represented by one live A/B residue pair.
- A/B low planes scale with `num_mat`.
- reduced product state remains live until final CRT.
- grouped CRT partially compresses that product frontier.

The B428 normalized trace remains useful as an algorithmic extreme, but it must not be labeled "GEMMul8 memory behavior."

## 11. New hypothesis H429 — Axis Temporalization

> Under a fixed correctness target, finite-memory algorithms can trade simultaneous state for repeated work by temporalizing different independent axes. Which axis is best depends on state size, reuse, kernel efficiency, reduction structure, and transfer cost.

Current evidence:

- GEMMul8 memory-saving: m/n/k temporalization;
- Scheme-II conceptual decomposition: modulus/precision temporalization;
- FlashAttention: sequence/tile temporalization;
- Strata: request/phase/expert residency temporalization.

This may be a more general organizing principle than "offload versus recompute."

## 12. Validation / claim ceiling

Frozen artifacts:

- src/finite_ram_lab/gemmul8_source_trace.py
- tests/test_gemmul8_source_trace.py
- analysis/inputs/B429-GEMMUL8-SOURCE-BACKED-TRACE-v0.1.json
- docs/B429-GEMMUL8-SOURCE-BACKED-LIVE-STATE-TRACE.md

Source-backed facts are pinned to upstream commit 603b52363715796a0af5e4aa1ed8d386349b4251.

The Python model mirrors the inspected INT8-real GEMM workspace formulas only. It is not a general GEMMul8 simulator.

No physical GPU run occurred.

## 13. Next bounce

B430 should model **axis temporalization** explicitly.

Minimum experiment:

1. take a symbolic GEMM state volume (m,n,k,p);
2. enumerate legal block vectors;
3. define workspace W(b);
4. define call count and traffic penalties;
5. compare:
   - m/n/k-only blocking;
   - p-only streaming;
   - hybrid m/n/k/p blocking;
6. solve tiny cases exactly;
7. fuzz a greedy/heuristic controller against exact optima.

Do not claim p-axis blocking is legal for GEMMul8 until a correctness-preserving incremental CRT state is explicitly specified.
