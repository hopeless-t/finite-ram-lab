# B461 — Obligation–Residency Separation Receipt

Status: **PASS / SOFTWARE-EXACT MODEL**
Date: 2026-10-02

## Frozen execution

Workflow: B461 Obligation Residency
Run: 36923780897
Job: 110575961631
Head: 456c129e7c093a4953230cdc50c43e81a83bc0fd
Artifact ID: 11193330348
Artifact ZIP digest: sha256:1595f8e1b236a443f92f3a12a462185944fd9dc7f720264cb5ab186c3c1332e8
Panel JSON SHA256: 4810bd6e5cb11f36fe3c328a6acad64c9720ddaead2ece35eb2021361f493ef6

Targeted tests:
- 6 tests
- 6 PASS
- runtime 0.023 s

## Exact CRT bite

The frozen 32x32 deterministic panel used seed 461 and residue-lane prefixes from:

`[127,125,121,119,113,109,107]`.

Conservative output bound:

`B = 934`.

Every tested lane count 2..7 satisfied the CRT uniqueness gate and reconstructed the exact integer GEMM.

| lanes | all-resident peak | streamed peak | reduction | fraction |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 4,096 B | 3,072 B | 1,024 B | 25.00% |
| 3 | 6,144 B | 4,096 B | 2,048 B | 33.33% |
| 4 | 8,192 B | 5,120 B | 3,072 B | 37.50% |
| 5 | 10,240 B | 6,144 B | 4,096 B | 40.00% |
| 6 | 12,288 B | 7,168 B | 5,120 B | 41.67% |
| 7 | 14,336 B | 8,192 B | 6,144 B | 42.86% |

These are logical intermediate representation bytes under the frozen model, not measured RSS.

## Scientific interpretation

The exact result obligation is preserved while simultaneous representation residency is reduced.

The constructive invariant is the incremental CRT fold state:

`(x mod M, M)`.

Once a residue lane has been folded into that state, retaining the lane itself is unnecessary for the future exact reconstruction obligation.

This establishes one exact software instance of H461:

> Obligation is not identical to simultaneous residency.

## Cross-domain claim boundary

The same structural question is recorded for:

- ternary model execution;
- Kitten review microsharding.

But they are classified as EMPIRICAL_CAPABILITY, not EXACT.

B461 does not transfer CRT's mathematical guarantee into those domains.

## Claim ceiling

**SOFTWARE_EXACT_LOGICAL_RESIDENCY_ONLY**

Not established:

- physical RSS reduction;
- speedup;
- production Ozaki kernel behavior;
- ternary/BF16 exact equivalence;
- exact reconstruction of sharded review semantics.

## Next research edge

B462 should test whether the representation schedule difference survives a fresh-process physical peak measurement.

Primary metric:

`normalized peak RSS growth`.

Use:
- matched reference/treatment processes;
- order balancing;
- exact semantic/result gate before physical interpretation;
- rare positive outlier biopsy rather than immediate broadening.
