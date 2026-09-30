# MATH-024 — Pre-VERIFY stock bound and the 65-touch theorem

## Question

B405 R8 produced one CLEAN identity that remained in NORMALIZING for all
64 allowed touches:

- 64 complete measured touches;
- no measured target direct Q64;
- no measured PTE growth;
- no CPU mismatch;
- no worker error;
- critical observer probes had zero missed hits at the block level.

This must not be called TARGET_FAIL. The target transaction was never verified.

The immediate question is narrower:

> Can a valid natural pre-VERIFY memcg stock state require touch 65 before the next direct Q64?

## Source-level stock invariant

For one memcg on one CPU, Linux `consume_stock()` searches the per-CPU memcg-stock slots. If the matching slot contains at least `nr_pages`, it subtracts exactly that amount.

For a one-page charge, `try_charge_memcg()` uses:

```text
batch = max(MEMCG_CHARGE_BATCH, nr_pages)
```

and the Chapter-II kernel has:

```text
MEMCG_CHARGE_BATCH = 64
```

When the direct batch charge succeeds, the excess is returned to the per-CPU stock by:

```text
refill_stock(memcg, batch - nr_pages)
```

so a measured one-page primer normally installs:

```text
64 - 1 = 63
```

cached pages.

This is the already-frozen verified invariant:

```text
R0 = 63
```

after a measured direct-Q64 primer.

## Why natural pre-VERIFY stock can be 64

`refill_stock()` behaves differently when the same memcg already has a slot on that CPU.

It computes:

```text
stock_pages = old_stock_pages + nr_pages
```

and drains the slot only when:

```text
stock_pages > MEMCG_CHARGE_BATCH
```

—not when it is equal.

Therefore the legal stock interval is:

```text
0 <= S <= 64
```

before the experiment has established its own measured primer.

This does not change the verified-primer result `R0 = 63`.

The distinction is:

- **natural/pre-VERIFY state:** `S in [0,64]`;
- **measured one-page Q64 primer:** reset to `R0 = 63`.

## 65-touch theorem

Let `S0` be the target memcg's usable stock on the selected stock CPU at the first measured data-page touch.

Assume:

1. `0 <= S0 <= 64`;
2. every measured operation faults exactly one previously untouched 4 KiB data page;
3. the worker remains on the selected CPU;
4. no PTE growth contaminates the measured sequence;
5. no worker error or duplicate touch occurs;
6. the critical direct-Q64 probe is complete;
7. no unobserved target refill adds stock without a corresponding direct charge.

Each successful stock-backed measured fault decreases the stock by one.

Therefore the first measured fault that cannot be satisfied from stock is:

```text
T = S0 + 1
```

and hence:

```text
1 <= T <= 65.
```

So:

```text
T <= 64  -> ordinary pre-VERIFY stock state
T == 65  -> PREVERIFY_S64 / MAX_STOCK_BOUNDARY
T > 65   -> current stock-bound model violation candidate
```

A drain can only reduce `S`, so a stock drain can move the boundary earlier, not later.

A source-grounded accounting release does not add stock and therefore also cannot move the boundary later.

## R8 specimen

R8 trial `0:0` ended as:

```text
NORMALIZE_EXHAUSTED after 64 touches
```

with no TARGET_FAIL.

Its raw trace also contains target-worker direct-Q64 activity on the stock CPU before NORMALIZE began.

The R8 protocol stopped at 64, so it did not observe touch 65.

Therefore R8 is compatible with, but does not yet prove:

```text
PREVERIFY_S64
```

The correct experiment is not to relabel R8. It is to extend a fresh, purpose-built normalization chase to touch 65.

## TX-NORMALIZE-BOUNDARY-CHASE-v1

Frozen design:

- 4 blocks;
- 8 fresh identities per block;
- 32 total identities;
- one fresh cgroup/worker per identity;
- fixed prep CPU -> stock CPU migration;
- target PID attribution from the trace task identity;
- one critical `page_counter_try_charge(...,64)` probe;
- primary boundary at touch 65;
- diagnostic continuation through touch 80 only if the primary bound is violated.

Classification:

```text
1..64  WITHIN_BOUND
65     MAX_STOCK_BOUNDARY
66..80 STOCK_BOUND_VIOLATION_CANDIDATE
none   BOUNDARY_NOT_FOUND
```

PTE growth, CPU mismatch, worker error, trace gaps, or multiple target Q64 events in one measured touch are classified separately.

## Sample-size note

R8 produced one 64-touch exhaustion specimen among 16 identities.

That historical fraction is not treated as a population probability.

For planning only, a Jeffreys update:

```text
Beta(0.5, 0.5) -> Beta(1.5, 15.5)
```

gives an approximately 81% posterior-predictive probability of seeing at least one recurrence in 32 additional identities.

This is design sensitivity only.

## Falsifiers

The current bound model is falsified by a valid specimen with:

- complete direct-Q64 probe coverage;
- clean PTE receipt;
- correct CPU;
- correct worker touch sequence;
- one process in the target cgroup;
- no target direct Q64 through touch 65.

If the first target Q64 appears at touch 66 or later, preserve the specimen as `STOCK_BOUND_VIOLATION_CANDIDATE` and continue only for diagnostic localization. Do not rewrite it as ordinary normalization.

## Claim ceiling

This experiment studies initial-state stock geometry.

It does not certify transactional reliability and does not estimate a population failure rate.
