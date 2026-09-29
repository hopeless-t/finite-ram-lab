# MATH-011 — Two-Touch PTE/Stock State Discriminator

> **Status:** MECHANISM DERIVATION / PROSPECTIVE
> **Depends on:** MATH-009 and G0 v1
> **No run launched.**

## 1. Idealized variables

Let:

- `R` = usable same-CPU memcg stock pages immediately before the measured first write;
- `I=0` = no new page-table memory required by first fault;
- `I=1` = first fault requires one newly charged page-table page before data allocation.

Linux v7.0 source establishes the relevant order:

`pte_alloc()` before `alloc_anon_folio()`

and page-table allocation can reach the same `consume_stock()` path.

Under the one-new-PTE-page idealization, the first write consumes:

`1 + I`

stock pages before any later touch.

## 2. First-touch exact-zero condition

Ignoring unrelated charge/uncharge activity:

`ZERO_FIRST <=> R >= 1 + I`

Therefore:

- existing PTE (`I=0`): exact-zero requires R>=1;
- new PTE (`I=1`): exact-zero requires R>=2.

If an arm only changes the probability that a new PTE page is required, then:

`P(ZERO | arm) = P(R>=2) + P(I=0 | arm) * P(R=1)`

Hence the exact-zero rate difference between two arms is:

`Delta ZERO = Delta P(I=0) * P(R=1)`

MEMCG-005G-F observed:

`Delta ZERO ~= +5.1413 percentage points`

between CAP10+ and CAP8/9.

Under a pure one-PTE mediation model, this implies the necessary lower bound:

`P(R=1) >= 5.1413%`

because `|Delta P(I=0)| <= 1`.

This is a mechanism constraint, not an estimate of the actual R=1 probability.

## 3. One-step conditional biopsy

After a valid first-touch exact-zero event, issue exactly one additional adjacent worker touch.

Record:

- second-touch memory.current delta;
- VmPTE immediately before and after the second touch.

Define:

`NEXT_Q64 := second_touch_delta_pages in [60,68]`

If the first touch consumed the final stocked charge, the second touch should require a fresh Q64 batch.

## 4. Sharp state predictions

Assume the second adjacent page does not require another new page-table page.

### Case A — first fault did not grow page tables

Receipts:

- `VmPTE_first_delta = 0`
- first touch = delta0
- second touch = Q64

Ideal inference:

`R = 1`

### Case B — first fault grew page tables

Receipts:

- `VmPTE_first_delta > 0`
- first touch = delta0
- second touch = Q64

Ideal inference under one extra charged PTE page:

`R = 2`

Thus the same observed depth1 morphology should shift its required pre-target stock by one page depending on page-table state.

This is a falsifiable prediction.

## 5. Boundary guard

The second adjacent page can itself cross into a new PTE table in a rare geometry.

Therefore also record:

`VmPTE_second_delta`

If `VmPTE_second_delta > 0`, do not use that specimen for the simple R=1/R=2 inference.

Keep it as a separate boundary phenotype.

## 6. Why this matters for prior biopsy data

MEMCG-005G-A found among 28 valid REMOTE_LOW exact-zero specimens:

- depth1: 22/28 = 78.57%
- deeper: 6/28

A dominant depth1 morphology is qualitatively compatible with a natural stock distribution concentrated near the minimum stock needed to make the measured first touch exact-zero.

MATH-011 makes that qualitative observation prospectively testable:

depth1 plus first-fault VmPTE state predicts whether the candidate pre-target stock was one or two pages.

The historical 22/28 does not by itself distinguish those two cases because VmPTE was not measured.

## 7. Minimal implementation consequence

No C worker change is required.

The existing worker increments `touched` and can accept another GO command.

Controller logic only:

1. record VmPTE_pre;
2. issue first GO;
3. record first delta and VmPTE_post1;
4. if first is exact-zero:
   - record before-second state;
   - issue exactly one second GO;
   - record second delta and VmPTE_post2;
5. stop worker.

This biopsy occurs after the frozen primary first-touch endpoint, so it does not alter the primary measurement.

## 8. Falsification outcomes

The simple one-PTE/low-stock model is weakened if, prospectively:

- exact-zero is not associated with VmPTE state at all;
- ZERO + NEXT_Q64 specimens show incompatible VmPTE transitions;
- second-touch non-Q64 behavior dominates despite stable CPU and no second PTE growth;
- nonzero anomalous morphologies explain the signal instead.

## 9. Council result

Add a failure-only one-step biopsy to G0 v1.

It has high information value because it converts a binary rare event into a state-discriminating specimen while preserving the unchanged worker and the primary endpoint.

Hosted research only.
No local-PC execution.
