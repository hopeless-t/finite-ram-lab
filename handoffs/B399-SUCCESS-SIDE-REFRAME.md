# B399 — Success-side theory reframed

## Status

RETROSPECTIVE REFRAME COMPLETE / NO NEW PHYSICAL RUN.

## Historical metric

MEMCG-005F REMOTE_LOW:
- first-touch Q64 121/123 = 98.374%
- first-touch zero 2/123 = 1.626%

That 1.6% is no longer treated as irreducible mechanism failure.

## New interpretation

REMOTE_LOW is a cheap predictor of favorable initial hidden phase, not proof of state.

Evidence:
- G-A: 28/28 first-touch zero specimens later reached Q64 by touch65
- MEMCG-004: arbitrary startup phase can be normalized by waiting for an observed fresh Q64
- controlled-spawn: 55/55 primer-qualified terminal patterns match
- recurrent -17 is LRU release contamination, not stock consumption
- OBS-006 corrected run: 14 MASKED_Q64_PASS / 2 STOCK_STATE_LOST

## OBS-006 consequence

Q64 success token changes from:

memory.current == +64

to direct charge-side receipts:
- page_counter_try_charge(64)
- refill_stock(63)
- PTE clean
- no unexpected state-invalidating transition

14/14 state-preserved OBS-006 trials recognized Q64 even when net memory.current was deliberately +47.

The two non-pass trials were correctly rejected because the stock state changed unexpectedly.

## New success architecture

predict -> normalize -> verify -> execute -> commit

REMOTE_LOW remains a fast-path admission hint.

Correctness boundary becomes a verified transactional state.

Unexpected refill/drain/PTE/CPU mismatch:
INVALIDATE -> RE-PRIME

not target failure.

## 100% target

Do not conflate:
- first-attempt completion
- eventual completion
- accepted-result correctness

The primary engineering target should be:

P(correct result | protocol emits SUCCESS)

with fail-closed handling of uncertain state.

## Documents

- docs/OBS-006-MASKED-Q64-OBSERVER-RESULT.md
- docs/MATH-017-SUCCESS-SIDE-REFRAME.md

## Next

Design the re-prime state machine and integrate OBS-006 charge receipts into controlled-spawn.

No large b63 certification run until that protocol is implemented and preflighted.