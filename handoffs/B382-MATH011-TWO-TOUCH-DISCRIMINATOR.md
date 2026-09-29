# B382 — Two-touch PTE/stock state discriminator

## Status

Research-only bounce complete.

No hosted scientific run launched.
No local-PC execution.

## New derivation

Let:
- R = same-CPU usable memcg stock immediately before first target write;
- I=0 if no new page-table charge is required;
- I=1 if one new charged page-table page is required before data allocation.

Linux v7.0 source gives:

`pte_alloc()` before `alloc_anon_folio()`

and page-table charge reaches the same per-CPU `consume_stock()`.

Ideal first-touch exact-zero condition:

`ZERO_FIRST <=> R >= 1 + I`

Under a pure one-PTE mediation model:

`Delta ZERO = Delta P(I=0) * P(R=1)`

Observed G-F high-vs-low exact-zero difference:

`+5.1413 percentage points`

Therefore a necessary condition for that pure mechanism is:

`P(R=1) >= 5.1413%`

This is a lower bound, not an estimate.

## Failure-only one-step biopsy

For a valid first-touch exact-zero specimen:

1. record first VmPTE delta;
2. issue exactly one additional adjacent worker touch;
3. record second memory.current delta;
4. record second VmPTE delta.

Define:
`NEXT_Q64 := second delta in [60,68]`

Ideal classifications:

### Candidate R=1
- first VmPTE delta = 0
- first touch = zero
- second touch = Q64
- second VmPTE delta = 0

### Candidate R=2
- first VmPTE delta > 0
- first touch = zero
- second touch = Q64
- second VmPTE delta = 0

Interpretation:
the first fault consumed one additional charged PTE page before data.

### Boundary phenotype
- second VmPTE delta > 0

Do not use for simple R=1/R=2 inference.

## Historical motivation

MEMCG-005G-A exact-zero biopsy:
- 28 specimens
- depth1 = 22/28 = 78.57%

Historical data lacked VmPTE, so depth1 could not separate:
- existing-PTE / R=1
from
- new-PTE / R=2.

B382 makes that distinction prospective.

## Worker perturbation

None required.

Existing MEMCG-005D worker already supports sequential GO touches and increments its page index.

The biopsy occurs strictly after the primary first-touch endpoint.

## Updated design

G0 v1 now includes the one-step biopsy:

`docs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.md`

Mechanism derivation:

`docs/MATH-011-TWO-TOUCH-PTE-STOCK-DISCRIMINATOR.md`

## Next boundary

Implement/launch G0 Stage A only after explicit Human hosted-compute approval.

Recommended Stage A:
16 blocks / 960 candidates.

Large 5760-candidate G-G remains deferred.
