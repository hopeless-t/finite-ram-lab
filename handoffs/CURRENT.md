# CURRENT

> Latest bounce: B410
> Stage: MONTE CARLO AGE-DECOUPLING EXPERIMENT SELECTED
> Stop: PHYSICAL PAUSE / READY FOR SUCCESSOR TRANSACTIONAL-SPAWN RUNNER

## Chapter II objective

Capture an unexplained verified-epoch boundary shift and discriminate whether its hazard is driven primarily by:

- measured touch activity;
- wall-clock exposure;
- boundary-local finite-state transitions;
- or a still-unobserved mechanism.

## Boundary invariant

After verified direct Q64:

R_0 = 63

and, under a clean uninterrupted epoch:

R_t = 63 - t.

Therefore the canonical next direct-Q64 boundary is:

T_0 = 64.

Define:

Delta = T - 64.

Any complete unexplained Delta != 0 is frozen as an evidence specimen.

## B406-B408 observer stack

Implemented:

- TRANSACTION-RECEIPT-PACKET-v2
- epoch-local owner_counter
- touch-age and wall-clock-age telemetry
- source-grounded RELEASE_ONLY classification
- transaction_epoch_archive
- re-prime clears observer authority
- native FRL_TX marker wrapper around the frozen Chapter-I _touch()

Synthetic replay/observer CI passed.

## B409 rare-transition capture

Frozen:

- specs/TX-BOUNDARY-DEVIATION-HUNT-v1.json
- docs/MATH-022-BOUNDARY-INVARIANT-RARE-TRANSITION-CAPTURE.md

Rare specimen:

UNEXPLAINED_BOUNDARY_DEVIATION

requires:

- verified Q64 start
- complete trace
- CPU/worker clean
- no PTE growth
- no drain
- no known state-changing antecedent
- owner releases absent or positively classified
- T != 64

## B410 Monte Carlo experiment selection

Reproducible MC:

- src/finite_ram_lab/tx_age_decoupling_mc.py
- tests/test_tx_age_decoupling_mc.py

Frozen result:

- analysis/inputs/TX-AGE-DECOUPLING-DESIGN-MC-v1.json

Narrative:

- docs/MATH-023-AGE-DECOUPLING-DESIGN-MONTE-CARLO.md

Handoff:

- handoffs/B410-MONTE-CARLO-AGE-DECOUPLING-DESIGN.md

The MC is design sensitivity only.

It does not estimate the real unexplained-deviation rate from historical 49/72 or 55/55 data.

Planning ranges:

- LOW: 0.1%..1%
- CENTRAL: 0.2%..5%
- HIGH: 1%..10%

## Selected Stage A

Spec:

- specs/TX-AGE-DECOUPLING-v1.json

Use b63 only.

16 identities:

- FAST x4
- HOLD32 x12

Four randomized blocks:

- 1 FAST
- 3 HOLD32

Target wall-clock exposure ratio:

F = 16

while measured-touch count is unchanged.

After B404/B405 provide physical FAST timing:

tau_fast = median VERIFIED -> canonical boundary duration

then:

dwell ~= 15 * tau_fast

after post-primer touch 32.

## Monte Carlo result

Central sensitivity:

FAST4 + HOLD12, F=16:

- balanced TOUCH/TIME discrimination ~= 81.1%
- P(any deviation | TIME) ~= 77.6%
- P(any deviation | TOUCH) ~= 19.8%

20 identities raises balanced discrimination only to about 82.2%.

24 raises it only to about 82.5%.

Therefore start with 16.

## Adaptive Stage B

Open only if Stage-A HOLD32 captures at least one complete unexplained boundary deviation.

Then run:

- HOLD8 x4
- HOLD32 x4
- HOLD56 x4

using the same dwell duration.

Central MC:

if TOUCH true:
- Stage-A trigger ~= 15.5%
- expected total identities ~= 17.9
- >=2 Stage-B positions with events conditional on opening ~= 2.9%

if TIME true:
- Stage-A trigger ~= 77.2%
- expected total identities ~= 25.3
- >=2 Stage-B positions with events conditional on opening ~= 59.0%

## Delta fingerprint

If a full-drain-like event occurs during the dwell:

- HOLD8 -> Delta about -55
- HOLD32 -> Delta about -31
- HOLD56 -> Delta about -7

If a hidden one-page consumption occurs instead:

- Delta about -1 independent of hold position.

Therefore Stage B converts a rare event into a position-dependent geometric fingerprint.

## Decision

Do not use the first discovery run as a passive fixed-tempo hunt.

After validation, use randomized age decoupling:

FAST x4 + HOLD32 x12.

Physical order:

1. implement successor transactional-spawn runner
2. B404 protocol smoke
3. B405 perturbation matrix
4. TX-AGE-DECOUPLING Stage A
5. Stage B only if triggered
6. passive hazard mapping later
7. reliability certification last

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
No perturbation matrix.
No age-decoupling run.
No reliability certification.
