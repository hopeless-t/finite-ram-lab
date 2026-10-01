# B431 — FlashAttention Source-Backed Future-State Trace v0.1

Status: **source-backed structural model + numerical recurrence validation**. No GPU benchmark ran.

Upstream source pin:

- Dao-AILab/flash-attention
- commit 616b0e8abab13b87b01525b3916d5a863ab02ae0

## 1. Cross-domain test

B431 tests whether the Live-State Frontier vocabulary, developed while studying Ozaki/GEMMul8, can describe an unrelated exact algorithm without inventing a new semantic category.

It can.

FlashAttention forward maps to the existing moves:

- REORDER: process attention by Q/KV tiles;
- REDUCE: fold each score tile into a smaller running state;
- RELEASE: discard score-tile state after it has contributed to the running state.

No new B426 state transformation was required.

## 2. Source-backed running state

The inspected FlashAttention source exposes:

- a score accumulator tile: acc_S;
- online softmax row_max;
- online softmax row_sum;
- an output accumulator: acc_O.

The forward path:

1. forms one score tile;
2. masks/modifies it;
3. calls online_softmax(acc_S);
4. obtains row_scale;
5. rescales prior acc_O when the running row maximum changes;
6. converts the normalized score tile into P-like state;
7. multiplies/accumulates against V;
8. continues with the next KV block.

The softmax implementation stores row_max and row_sum in running state rather than the full history of scores.

## 3. Future-Sufficient State lemma for exact softmax

For one query row, suppose a processed prefix has scores s_i and value vectors v_i.

Define:

m = max_i s_i

l = sum_i exp(s_i - m)

o = sum_i exp(s_i - m) v_i.

The retained state is:

phi(prefix) = (m, l, o).

For a new block B with scores/value pairs (s_j, v_j), let:

m' = max(m, max_j s_j).

Then:

l'
=
exp(m-m') l
+
sum_j exp(s_j-m')

and:

o'
=
exp(m-m') o
+
sum_j exp(s_j-m') v_j.

The final exact attention row is:

O = o' / l'

and:

LSE = m' + log(l').

Therefore the old individual scores and value-weight products are not needed after they have been folded into (m,l,o).

This is an explicit instance of the B426 Future-Sufficient State rule:

Future(prefix, remaining_KV)
=
Future(phi(prefix), remaining_KV).

## 4. Source correspondence

The source recurrence matches the lemma:

- row_max stores m;
- row_sum stores l;
- row_scale = exp(old_max - new_max);
- rescale_O multiplies prior acc_O by row_scale;
- current normalized score tile is then consumed in the V multiplication;
- final normalization derives O and LSE.

This is stronger evidence for the framework than a superficial memory analogy: the implementation exposes the exact sufficient-state recurrence.

## 5. Structural frontier

A naive materialized score state for one head has:

N_q * N_k * score_element_bytes

elements/bytes.

In the tiled implementation the avoidable score state is bounded by the active tile:

B_m * B_n * score_accumulator_bytes,

while the running exact summary for a query tile contains approximately:

- 2 * B_m FP32 statistics;
- B_m * d_v output-accumulator values.

This is intentionally a structural model; register distribution, shared-memory staging, Q/K/V tiles, pipelines, and implementation-specific temporary state must be added for a full hardware footprint.

## 6. Frozen example

For structural units:

- B_m=128
- B_n=128
- d_v=128
- FP32 score/output accumulators and stats

the modeled pieces are:

- active score tile: 65,536 bytes
- row stats: 1,024 bytes
- output accumulator: 65,536 bytes
- modeled active frontier: 132,096 bytes.

For comparison, a fully materialized 4096x4096 FP32 score matrix is 67,108,864 bytes.

This comparison isolates score-state geometry only. It is not a claim that FlashAttention total memory is 508x smaller, since Q/K/V/O, pipelines, and concurrent tiles are outside this simple frontier.

## 7. Numerical recurrence validation

The lab implementation:

- src/finite_ram_lab/flashattention_future_state.py
- tests/test_flashattention_future_state.py

implements the mathematical running summary independent of CUDA.

Validation during authoring:

- fixed two-block example PASS;
- all block sizes for a fixed row PASS;
- deterministic 10,000 randomized partition cases PASS.

For each randomized case:

1. compute stable full softmax and weighted output;
2. partition the same sequence into random block sizes;
3. update only (row_max,row_sum,weighted_output_accumulator);
4. finalize output and LSE;
5. compare with the full reference.

All cases matched within floating tolerance.

This validates the recurrence, not the performance or exact floating-point behavior of any specific GPU kernel.

## 8. Cross-domain result

Ozaki-II/GEMMul8 and FlashAttention now fit the same high-level pattern:

### Ozaki/CRT

local residue/product state
-> exact reduction/reconstruction state
-> release old local product state.

### FlashAttention

local score tile
-> exact online-softmax/output state
-> release old score tile.

The summary states differ completely mathematically, but both implement:

**EPHEMERAL STATE -> FUTURE-SUFFICIENT STATE -> RELEASE**

This appears to be a meaningful common primitive.

## 9. Refinement to Live-State Frontier theory

The key unit is not merely a tensor or allocation.

It is an **information obligation**:

> What information from the past can still change any legal future output?

A state may die as soon as that obligation has been transferred into a smaller sufficient representation.

This gives a sharper definition of logical liveness than reference-count liveness.

Two objects can still be technically available while one is already semantically dead because its effect has been completely summarized.

## 10. New hypothesis H431 — Semantic Liveness

> Peak memory can be reduced by identifying the earliest point at which an intermediate becomes future-redundant, not merely the point at which the implementation stops referencing it.

This suggests a compiler/runtime opportunity:

1. derive/prove future-sufficient summaries;
2. shorten semantic live intervals;
3. schedule placement only after this shortening.

This is stronger than traditional lifetime analysis when a nonlinear summary can replace the original state.

## 11. Model survival

B428's existing concepts were sufficient:

- TraceState
- REDUCE_AND_RELEASE
- live interval
- logical bytes
- physical bytes
- summary_sufficient.

No FlashAttention-specific semantic state category was necessary.

That is a positive cross-domain result for the model.

## 12. Next bounce B432

A useful next test is Strata because it attacks a different layer.

FlashAttention and Ozaki mainly demonstrate logical-frontier rewriting.

Strata should test whether the same framework also handles:

- unchanged logical model information;
- compressed representation;
- tier placement;
- shared physical copies;
- phase-specific residency;
- idle lifetime contraction.

If B432 also fits without changing the core schema, the model will have survived:

1. numerical precision emulation;
2. exact attention;
3. real LLM residency management.

That would justify freezing a Live-State Frontier taxonomy v0.2.
