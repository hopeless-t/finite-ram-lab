# CURRENT

> Latest bounce: B399
> Stage: SUCCESS-SIDE THEORY = VERIFIED TRANSACTION, NOT FIRST-TOUCH LUCK
> Stop: PHYSICAL PAUSE / READY FOR RE-PRIME STATE-MACHINE DESIGN

## Historical 1.6%

MEMCG-005F REMOTE_LOW:
- Q64 first touch 121/123 = 98.374%
- zero first touch 2/123 = 1.626%

Interpretation updated:
the 1.6% is not an established irreducible mechanism error.

## Current success model

REMOTE_LOW is an admission predictor only.

Correctness protocol:
predict -> normalize -> verify -> execute -> commit

Verified Q64 reset token:
- page_counter_try_charge(64)
- refill_stock(63)
- PTE clean
- no unexpected state-invalidating transition

## Supporting evidence

- G-A first-touch zero: 28/28 later Q64 by touch65
- MEMCG-004 calibrated reset phase: exact R64 in 4/4
- controlled-spawn primer-qualified terminal match: 55/55
- OBS-005 closes dominant -17 LRU contamination
- OBS-006 corrected run: MASKED_Q64_PASS 14/16, STOCK_STATE_LOST 2/16
- all 14 state-preserved OBS-006 trials correctly identify deliberately masked Q64 (+64-17 = net +47)

## 100% target

Primary engineering target:
P(correct | emitted SUCCESS)

Fail closed:
unexpected refill / drain / PTE / CPU mismatch => INVALIDATE and RE-PRIME.

Do not define success by raw memory.current delta.

## Docs

- docs/OBS-006-MASKED-Q64-OBSERVER-RESULT.md
- docs/MATH-017-SUCCESS-SIDE-REFRAME.md

## Next

Design and preflight transactional re-prime controlled-spawn.

No large b63 certification run yet.

## Authority

PAUSE.
No local-PC execution.
No paid runner.