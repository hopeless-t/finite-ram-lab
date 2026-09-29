# MATH-015 — The -17 latent component and asynchronous accounting emission

> **Status:** RETROSPECTIVE / SOURCE-GROUNDED HYPOTHESIS
> **Physical execution:** NONE
> **Inputs:** controlled-spawn v2 raw 72 identities, MATH-014 census, Linux v7.0 memcontrol source.
> **Claim ceiling:** strong observational support for a 17-page pre-existing accounted component; exact kernel origin remains unresolved until direct tracing.

## 1. Why revisit -17

Controlled-spawn v2 contained 23 trials with a negative measured delta.

Distribution:
- -17 pages: 20
- -13 pages: 1
- -3 pages: 1
- -2 pages: 1

No trial contained more than one negative measured event.

The six primer-qualified trials with negative bait deltas still produced the exact predicted b62/b63/b64 terminal phase.

Therefore a negative memory.current delta is not equivalent to consuming or refilling the Stock-CPU phase.

## 2. Pre-current has discrete modes

The 72 post-migration pre-calibration memory.current values are highly discrete.

Dominant support:
- 98 / 99 / 100
- 114 / 115 / 116 / 117
- 161 / 162 / 163
- 179 / 180

A compact descriptive lattice is:

pre_current ~= B + 17*Z17 + 64*Z64

with B in {97,98,99,100} and Z17,Z64 in {0,1}.

This is not yet a physical decomposition. It is a low-description-length representation of observed starting states.

Fit:
- 68/72 identities exactly on the lattice
- first four blocks: 33/36 exact
- last four blocks: 35/36 exact

The recurrence in held-out later blocks argues against a one-block visual coincidence.

## 3. The +17 mode predicts -17

Define the +17 modal region from the first-half pattern as 114..117 and 179..180.

First four blocks:
- +17 mode: 8/12 had a -17 event
- other modes: 1/24
- Fisher two-sided p ~= 1.29e-4

Last four blocks, without changing the region:
- +17 mode: 11/14 had a -17 event
- other modes: 0/22
- Fisher two-sided p ~= 6.06e-7

All eight blocks:
- +17 mode: 19/26
- other modes: 1/46
- OR ~= 122.1
- Fisher two-sided p ~= 9.77e-11

This association is much stronger than an arm-specific explanation.

## 4. Subtracting 17 lands on clean modes

For the 20 -17 specimens, subtract 17 from their starting pre_current.

Results:
- 17/20 land exactly on a pre_current value observed in clean trials
- 19/20 land within one page of clean support

Examples:
- 115 -> 98
- 116 -> 99
- 179 -> 162
- 180 -> 163

This is the signature expected if a 17-page component was already included in memory.current before the measured sequence and later disappeared as one accounting event.

## 5. Event position is nearly phase-independent

Among the 20 -17 events, global measured-touch index from the start of calibration is:
- touch 14: 11 events
- touch 13: 5
- touch 18: 1
- touch 11: 1
- touch 20: 1
- touch 1: 1

Thus 16/20 occur at touch 13 or 14 and 18/20 occur between touches 11 and 20.

When the Q64 primer appears at touch 1, the same event moves into bait phase around bait 12-13 rather than staying attached to calibration.

Therefore the event is not naturally described as a special calibration touch. A time- or external-activity-triggered asynchronous event is more plausible.

No touch timestamps were recorded, so a literal time-delay law is not established.

## 6. Linux v7.0 candidate origins

memory.current can fall through multiple paths.

Candidate A — per-CPU stock drain:
- drain_stock reads the exact cached stock page count
- calls memcg_uncharge(old, stock_pages)
- zeroes the stock
- it can be reached from refill_stock slot replacement/overflow or drain_all_stock via drain_local_memcg_stock
- there is no periodic timer in the stock work itself

Candidate B — ordinary folio uncharge:
- uncharge_batch aggregates freed folio pages
- calls memcg_uncharge(memcg, ug->nr_memory)
- this also lowers memory.current without consuming the Stock-CPU residual stock used by the measured data fault

Candidate C — other direct uncharge:
- objcg release, refill fallback and other memcg_uncharge callers remain possible

## 7. Generic folio-batch size does not explain 17

Linux v7.0 defines FOLIO_BATCH_SIZE = 31.

There is no generic 17-folio batch constant corresponding to the observed signature.

This weakens a trivial kernel-always-reclaims-17 explanation but does not eliminate an ordinary workload-specific 17-folio uncharge.

## 8. Current best mechanism hypothesis

H17-STOCK:
1. worker startup on preparation CPU P creates a target-memcg precharged stock component
2. after startup activity, 17 unused charged pages remain in that off-path component
3. the worker migrates to stock CPU S
4. S-side controlled phase proceeds independently
5. later, the P-side 17-page component is evicted/drained
6. memory.current emits -17
7. S-side terminal phase remains unchanged

This explains the +17 modes, one-time -17 emission, subtract-17 return to clean modes, terminal-phase preservation, and phase-independent global event position.

However it is not yet proven because ordinary folio uncharge can produce the same memory.current observation.

## 9. Falsification requirement

A direct accounting observer must record the target memcg and the memcg_uncharge call stack.

If H17-STOCK is correct, a -17 window should contain target memcg uncharge pages=17 with a drain_stock frame, likely via refill_stock or drain_local_memcg_stock.

If folio-uncharge is correct, the stack should contain uncharge_batch / __mem_cgroup_uncharge_folios and no drain_stock frame.

If neither appears, the observer is incomplete or another accounting path is responsible.

## 10. Scientific consequence

Do not scale b63 reliability yet.

The next information-maximizing experiment is an observer validation, not more spawn trials.

The frozen 49/72 and conditional 55/55 results remain unchanged.
