# B410 — Monte Carlo selects adaptive age-decoupling hunt

## Status

COMPLETE / DESIGN MC / NO PHYSICAL RUN.

## Question

Which experiment should follow B404/B405 if the goal is to capture and classify the Chapter-II unexplained boundary deviation efficiently?

## Monte Carlo

Reproducible code:

- src/finite_ram_lab/tx_age_decoupling_mc.py
- tests/test_tx_age_decoupling_mc.py

Frozen summary:

- analysis/inputs/TX-AGE-DECOUPLING-DESIGN-MC-v1.json

Narrative:

- docs/MATH-023-AGE-DECOUPLING-DESIGN-MONTE-CARLO.md

The MC is a sensitivity design study, not an empirical posterior.

Historical controlled-spawn cannot identify the B400 unexplained-deviation rate.

Planning ranges:

- LOW: 0.1%..1%
- CENTRAL: 0.2%..5%
- HIGH: 1%..10%

## Chosen discovery experiment

TX-AGE-DECOUPLING-v1

Stage A:

- b63 only
- FAST x4
- HOLD32 x12
- total 16 identities
- four randomized blocks
- wall-clock exposure target F=16
- measured-touch count unchanged

Spec:

- specs/TX-AGE-DECOUPLING-v1.json

## Why 16, hold-heavy

Central MC:

FAST4 + HOLD12, F=16:

- balanced TOUCH/TIME model discrimination ~= 81.1%
- P(any unexplained deviation | TIME) ~= 77.6%
- P(any unexplained deviation | TOUCH) ~= 19.8%

Moving to 20 identities:

- balanced accuracy ~= 82.2%

Moving to 24:

- balanced accuracy ~= 82.5%

Therefore +25% to +50% samples buys little initial model discrimination.

Use 16 first.

## Dwell definition

After validated FAST timing exists:

tau_fast = median VERIFIED -> canonical boundary elapsed time

HOLD32 adds approximately:

15 * tau_fast

after post-primer touch 32.

Thus total wall-clock exposure is approximately 16x while touch count remains fixed.

No arbitrary millisecond dwell is frozen before physical timing exists.

## Adaptive Stage B

Open only if Stage-A HOLD32 captures at least one complete:

UNEXPLAINED_BOUNDARY_DEVIATION.

Then:

- HOLD8 x4
- HOLD32 x4
- HOLD56 x4

same dwell duration.

Central MC:

if TOUCH true:
- Stage-A trigger ~= 15.5%
- expected total identities ~= 17.9
- >=2 Stage-B positions with events conditional on opening ~= 2.9%

if TIME true:
- Stage-A trigger ~= 77.2%
- expected total identities ~= 25.3
- >=2 Stage-B positions with events conditional on opening ~= 59.0%

## Delta barcode

For a full-drain-like transition during dwell:

- HOLD8 -> Delta about -55
- HOLD32 -> Delta about -31
- HOLD56 -> Delta about -7

A one-page hidden consumption mechanism instead predicts approximately:

- Delta = -1 independent of hold position.

Thus Stage B turns event presence into a geometric fingerprint.

## Council convergence

Statistician:
- adaptive 16 + conditional 12 is more efficient than unconditional 24+.

Mechanist:
- hold intervention isolates wall-clock exposure from measured-touch count.

Observer reviewer:
- only complete B400/v2 unexplained deviations enter the model.

Falsification reviewer:
- FAST-only specimens are frozen/reproduced rather than forced into the TIME story.

Resource reviewer:
- no automatic Stage B; no automatic reliability scale-up.

Convergence:

Use adaptive age decoupling after validation.

## Physical order

1. implement successor runner
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
No physical experiment.
