# B427 — Common Exemplar Encoding

Status: **symbolic/software model only**. No physical benchmark was executed.

## 1. Why this bounce exists

B426 defined the Live-State Frontier model. B427 asks whether very different systems can be represented by the same transformation vocabulary without erasing the distinction between logical and physical memory.

The answer is yes, with one important refinement:

> The model needs both a logical frontier and a physical frontier.

## 2. Logical versus physical frontier

Let:

- L(t) = bytes of semantic state that future computation still requires;
- M_j(t) = physical bytes resident on memory tier j.

Then physical memory can be decomposed conceptually as:

M_physical(t)
=
L_encoded(t)
+ duplicate(t)
+ fragmentation(t)
+ workspace(t)
+ prefetch(t)
+ allocator/runtime reserve(t).

This matters because different systems attack different terms.

- Ozaki II and FlashAttention can reduce the logical/materialized frontier.
- PagedAttention mainly reduces fragmentation and duplicate physical residency.
- Strata changes placement, sharing, borrowing, and lifetime.
- Checkmate/DTR removes live physical state while retaining regeneration provenance.

Treating all of these as "memory reduction" hides the mechanism.

## 3. Ozaki Scheme I

For a simplified materialized-slice model with k slices:

P_I =
base + k(A_slice + B_slice) + accumulator.

The triangular GEMM count is:

G_I = k(k+1)/2.

This is intentionally a structural model, not a byte-accurate implementation model.

The key property is that increasing k widens the materialized precision frontier when all required slices remain resident.

Source:
https://arxiv.org/abs/2504.08009

## 4. Ozaki Scheme II

For s total moduli and r simultaneously resident residue pairs:

P_II =
base + r(A_residue + B_residue) + accumulator.

G_II = s.

If r is held fixed by streaming, P_II does not grow with the total number of moduli s.

This is the important structural distinction:

- more desired reconstruction work can increase time/compute;
- it need not increase simultaneous residue residency.

B427 validated this invariant across 10,000 deterministic randomized parameter combinations.

Source:
https://arxiv.org/abs/2504.08009

## 5. EmuGEMM

Ozaki-style precision emulation can still lose performance if intermediate state repeatedly travels through global memory.

EmuGEMM attacks a different dimension: fusion reduces redundant global-memory round trips.

Therefore:

- Scheme II primarily demonstrates frontier rewriting / ephemeral state;
- EmuGEMM demonstrates traffic reduction after that rewrite.

The two should not be collapsed into one "memory optimization" label.

Source:
https://arxiv.org/abs/2606.25453

## 6. FlashAttention

A naive attention-score matrix has an avoidable materialized component scaling as:

S_naive = N^2 * element_bytes.

A tile-local score block is:

S_tile = Br * Bc * element_bytes.

The full FlashAttention memory model includes Q/K/V/O and running statistics, so this is not a total-memory formula. It isolates the state that the tiled exact algorithm avoids materializing globally.

Example used only as an invariant test:

- N=4096;
- Br=Bc=128;
- same element size.

Then the score-state ratio is 1024:1.

This is not a benchmark claim. It shows the structural effect of replacing a full intermediate with tiled future-sufficient running state.

Source:
https://arxiv.org/abs/2205.14135

## 7. PagedAttention

PagedAttention preserves the logical KV information but changes physical representation and sharing.

The important distinction is:

L_KV approximately unchanged,

while

M_physical = L_KV + fragmentation + duplicate copies + allocator slack

is reduced.

This makes PagedAttention a canonical example of a technique that improves the physical frontier without necessarily shrinking the semantic information requirement.

Source:
https://arxiv.org/abs/2309.06180

## 8. Checkmate and DTR

Checkpoint/rematerialization changes the liveness decision.

A state can disappear from physical residency while remaining recoverable from retained ancestors.

This is modeled as:

DROP_REMATERIALIZE.

The exchange is:

less P/A
for
more C and possibly T.

Sources:
https://arxiv.org/abs/1910.02653
https://arxiv.org/abs/2006.09616

## 9. FlexGen

FlexGen is the clearest placement-oriented exemplar in this set.

It aggregates GPU, CPU, and disk and searches tensor-storage/access patterns under hardware constraints, with compression as an additional representation transformation.

This is mostly:

MOVE + COMPRESS

after the tensor graph is known.

Source:
https://arxiv.org/abs/2303.06865

## 10. Strata

Recent Strata work is interesting because it applies multiple moves inside one runtime:

- compressed KV -> COMPRESS;
- mmap experts -> MOVE / deferred residency;
- resident experts -> MOVE;
- shared host arena -> SHARE;
- cache lending -> REORDER / phase-local borrowing;
- per-GPU state ownership -> reduce duplication and ownership scope;
- idle unload -> lifetime contraction.

This makes Strata useful for testing the model under realistic mixed policies.

Current public project:
https://github.com/Niko1221/Strata

Shared-host-arena experiment:
https://github.com/Niko1221/Strata/issues/127

## 11. Phase-dependent state temperature

B427 freezes a simple phase-specific value density:

Theta_i(p)
=
accesses_i(p)
* max(0, slow_cost_i - fast_cost_i)
/
size_i.

A two-expert synthetic test demonstrates that ordering can reverse between phases:

- expert A is hotter during prefill;
- expert B is hotter during decode.

Therefore one globally fixed hotset is not generally equivalent to phase-aware residency.

This does not prove Strata's policy is optimal. It establishes a model condition under which phase-specific placement has a principled advantage.

## 12. Deduplication law

For one state object of size S duplicated across n processes:

M_before = nS.

If a shared canonical copy plus m bytes of per-process metadata is sufficient:

M_after = S + nm.

Potential savings:

Delta M = max(0, (n-1)S - nm).

This is the SHARE operation.

The same algebra applies to expert arenas, shared KV prefixes, code pages, immutable weights, and other canonical state.

## 13. Main result of B427

The strongest new conclusion is a separation of three questions:

1. **What information must future computation still possess?**
   - logical frontier.

2. **In what representation and how many copies does that information exist?**
   - physical frontier.

3. **Where and for how long are those physical bytes resident?**
   - placement/lifetime frontier.

This yields a hierarchy:

graph semantics
-> future-sufficient representation
-> schedule/liveness
-> sharing/dedup
-> physical placement
-> runtime migration.

A placement-only optimizer starts too late if an earlier rewrite is possible.

## 14. Software validation

Files:

- src/finite_ram_lab/live_state_exemplars.py
- tests/test_live_state_exemplars.py
- specs/LIVE-STATE-EXEMPLARS-v0.1.json

Validation during authoring:

- 9 unit tests PASS;
- 10,000 deterministic randomized Ozaki invariant cases PASS;
- Ozaki-I triangular GEMM invariant preserved;
- Ozaki-II fixed-resident-pair peak invariant preserved;
- phase-value ordering reversal test PASS;
- deduplication arithmetic test PASS;
- tiled-attention avoidable-state test PASS.

Claim ceiling remains SYMBOLIC_AND_SOFTWARE_MODEL_ONLY.

## 15. B428 candidate

The next useful step is no longer adding more named systems.

Instead, construct a **frontier compiler** that takes a state DAG annotated with:

- size;
- live interval;
- future-sufficient summary;
- regeneration edges;
- replica identity;
- memory-tier costs;
- phase-dependent reuse;

and emits:

- logical peak;
- physical peak;
- byte-seconds;
- transfer lower/upper estimates;
- safe release opportunities;
- exact placement for tiny windows;
- heuristic placement for larger windows.

Then feed the same compiler:

- Ozaki-I materialized slices;
- Ozaki-II streaming residues;
- FlashAttention tiled state;
- a minimal Strata expert-residency trace.

That would turn the theory into a reusable experimental instrument.
