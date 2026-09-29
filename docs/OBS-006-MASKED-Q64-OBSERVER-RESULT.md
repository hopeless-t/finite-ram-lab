# OBS-006 — Masked-Q64 charge-side observer result

> Status: CORRECTED RUN COMPLETE / MECHANISM OBSERVER SUPPORTED
> Valid run: 36627925282
> Launch commit: ce3a465e4b94f28b6b04ea32ed513e2484c72441
> Earlier run 36627449180: historical setup failure; scrub event-name mismatch caused 16/16 SCRUB_NO_FLUSH.

## Frozen corrected result

16 trials:

- MASKED_Q64_PASS: 14
- STOCK_STATE_LOST: 2

All 14 MASKED_Q64_PASS trials had the deliberately masked secondary receipt:

memory.current delta = +47 pages

while the direct charge-side chain showed:

- page_counter_try_charge(...,64)
- refill_stock(...,63)
- LRU flush / folios_put
- same-counter page_counter_uncharge(...,17)

Thus:

+64 charge -17 release = +47 net

The direct observer correctly identifies Q64 even when net memory.current is not +64.

## Two non-pass trials

Both were rejected as STOCK_STATE_LOST rather than misclassified as Q64 success.

Trial 0:0:
- unexpected refill during PRODUCER touch 1

Trial 1:0:
- unexpected refill during CONSUME touch 20
- another unexpected refill during PRODUCER touch 1

These are state-validity failures, not observer false positives.

## Meaning

The success token should no longer be:

net memory.current == +64

It should be the direct charge-side receipt:

page_counter_try_charge(64) + refill_stock(63)

with PTE and unexpected-state-transition guards.

memory.current becomes secondary corroboration only.

## Evidence

Corrected run raw manifest:

- file count: 88
- total bytes: 10,166,728
- content-set SHA-256:
  eeb0649e2a7eb9ece8e10752e170d2e016b086666161a64e8b74657e240c6dea

Aggregate artifact:
OBS-006-MASKED-Q64-OBSERVER-36627925282

Aggregate SHA-256:
eaeaea7302e6a83a23b0f4d7bdafd6668ad5afc5cf3e462736d0b70b7799b84e

## Consequence

OBS-006 separates two problems that were previously mixed:

1. observing Q64 correctly;
2. keeping the calibrated stock state alive long enough to execute the target transition.

The observer succeeded in all 14 trials whose planned stock state remained valid.

The next 100%-oriented design should therefore be fail-closed and transactional:
unexpected refill/drain/PTE transition invalidates the attempt and causes re-prime, rather than becoming a false failure or false success.
