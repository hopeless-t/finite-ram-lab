# MATH-023 — Monte Carlo Design for Touch/Time Decoupling

> Status: DESIGN MC COMPLETE / NO PHYSICAL RUN  
> Chapter: finite-ram-lab II  
> Inputs: B404-B409, OBS-006, boundary invariant T0=64  
> Purpose: choose the smallest experiment that best distinguishes touch-driven from wall-clock-driven unexplained boundary deviation.

## 1. Question

After a verified direct Q64, suppose an unexplained boundary deviation appears:

Delta = T - 64 != 0.

What is the cheapest next experiment that can distinguish:

- TOUCH mechanism — hazard follows measured page-touch activity;
- TIME mechanism — hazard follows wall-clock exposure while measured-touch count is held fixed?

The experiment should maximize mechanism discrimination rather than raw specimen count.

## 2. Important non-claim

Historical controlled-spawn cannot identify the B400 unexplained-deviation rate.

Therefore this Monte Carlo does **not** use a fitted posterior from the old 49/72 or 55/55 endpoints.

Instead it is a sensitivity design study with log-uniform baseline FAST per-epoch probability ranges:

- LOW: 0.1% .. 1%
- CENTRAL: 0.2% .. 5%
- HIGH: 1% .. 10%

These are planning priors only.

## 3. Competing models

Let p be the FAST per-epoch unexplained-deviation probability.

### TOUCH

The HOLD arm has the same measured-touch count, so:

p_hold = p_fast = p.

### TIME

Let F be total wall-clock exposure ratio relative to FAST.

Assuming a constant time hazard only for design sensitivity:

p_hold = 1 - (1 - p)^F.

This does not assert that the physical process is exponential. It gives the experiment a controlled design target.

## 4. Candidate designs

100,000 Monte Carlo draws per candidate.

Equal prior weight on TOUCH and TIME.

Bayesian model choice integrates over the same log-uniform p prior for each model.

Central sensitivity results:

| Design | Identities | F | Balanced model accuracy | P(any deviation | TIME) |
|---|---:|---:|---:|---:|
| FAST8 + HOLD8 | 16 | 8 | 69.9% | 53.6% |
| FAST8 + HOLD8 | 16 | 16 | 78.6% | 69.6% |
| FAST4 + HOLD12 | 16 | 8 | 72.8% | 62.2% |
| **FAST4 + HOLD12** | **16** | **16** | **81.1%** | **77.6%** |
| FAST4 + HOLD16 | 20 | 16 | 82.2% | 83.3% |
| FAST8 + HOLD16 | 24 | 16 | 82.5% | 83.4% |

The gain from 16 to 24 identities is small:

- balanced discrimination: about +1.5 percentage points;
- TIME-model detection: about +5.8 percentage points;
- sample count: +50%.

Therefore the 16-identity hold-heavy design has the best initial information/cost tradeoff.

## 5. Chosen Stage A

Freeze:

- FAST x4
- HOLD32 x12
- total 16 identities
- b63 only
- four randomized blocks
- each block contains 1 FAST + 3 HOLD32

Why b63?

It supplies a compact local barcode:

ZERO -> Q64

around the canonical boundary while using fewer terminal touches than b62 and more local confirmation than b64.

## 6. Exposure factor

Target:

F = 16.

Do not hard-code an arbitrary millisecond value before physical timing exists.

After B404/B405 validation, measure the median FAST elapsed time from VERIFIED to the canonical boundary:

tau_fast.

Then define approximately:

dwell = 15 * tau_fast

after post-primer touch 32.

This makes total wall-clock exposure approximately:

tau_hold ~= 16 * tau_fast

while leaving the measured-touch count unchanged.

The worker remains alive in the same epoch.

## 7. Why HOLD32 first

Touch 32 is intentionally central.

If a time-driven event destroys the residual stock during the dwell, the next direct Q64 may occur near touch 33.

For a full-drain-like transition:

Delta ~= 33 - 64 = -31.

That is a high-amplitude fingerprint, far from the ordinary -1 local shift.

It also leaves enough safe-span budget for post-event diagnostic windows.

## 8. Sensitivity of the chosen 16-identity design

### LOW planning range: 0.1% .. 1%

- balanced TOUCH/TIME discrimination: 71.8%
- P(any deviation | TIME): 48.6%
- P(any deviation | TOUCH): 5.8%

Interpretation:

if the mechanism is extremely rare, Stage A may simply see nothing.

That is expected and must not be called evidence of absence.

### CENTRAL: 0.2% .. 5%

- balanced discrimination: 81.1%
- P(any deviation | TIME): 77.6%
- P(any deviation | TOUCH): 19.8%

### HIGH: 1% .. 10%

- balanced discrimination: 91.1%
- P(any deviation | TIME): 97.8%
- P(any deviation | TOUCH): 43.3%

Thus the experiment becomes increasingly decisive if wall-clock exposure genuinely amplifies the unknown transition.

## 9. Adaptive Stage B

Do not spend position-localization samples unless Stage A gives a reason.

Trigger Stage B if:

> at least one complete UNEXPLAINED_BOUNDARY_DEVIATION occurs in HOLD32.

Stage B:

- HOLD8 x4
- HOLD32 x4
- HOLD56 x4

Use the same dwell duration.

Total additional identities: 12.

### Central MC

If TOUCH is true:

- Stage-A trigger probability: 15.5%
- expected total identities: 17.9
- conditional probability of events in >=2 Stage-B hold positions: 2.9%

If TIME is true:

- Stage-A trigger probability: 77.2%
- expected total identities: 25.3
- conditional probability of events in >=2 Stage-B hold positions: 59.0%

This gives the adaptive design useful behavior:

- under a touch-driven mechanism, it usually stops after 16;
- under a time-driven mechanism, it frequently opens the localization stage.

## 10. Delta fingerprint in Stage B

For a full-residual-loss event occurring during the dwell, the next measured touch becomes Q64.

Approximate fingerprints:

- HOLD8: T ~= 9, Delta ~= -55
- HOLD32: T ~= 33, Delta ~= -31
- HOLD56: T ~= 57, Delta ~= -7

If the observed Delta tracks hold position this strongly, a time-triggered residual-destruction mechanism becomes much more plausible.

By contrast, a hidden one-page consumption event can yield:

Delta = -1

regardless of hold position.

Therefore Stage B does not merely count events; it uses the **magnitude of the boundary shift** as causal geometry.

## 11. What if Stage A sees a FAST-only specimen?

Do not automatically open the dwell-position scan.

Freeze the FAST specimen.

First reproduce it in a new independent FAST identity.

A FAST-only unexplained deviation is evidence against the simple "only extra waiting causes it" story and may point toward:

- touch-driven hazard;
- background asynchronous activity already present at normal duration;
- a missing deterministic transition.

## 12. What if Stage A sees no specimen?

Do not jump directly to a large reliability run.

The result only constrains the chosen exposure regime.

Under the LOW sensitivity prior, even a TIME mechanism has about a 51% chance to escape Stage A.

The next decision should then use the observed physical FAST duration, trace overhead, and invalidator rate to choose between:

- increasing F;
- increasing HOLD identities;
- adding same-CPU competition;
- or declaring a bounded absence study.

## 13. Experimental order

The Monte Carlo changes the discovery experiment, not the validation prerequisites.

Physical order remains:

1. successor transactional-spawn runner implementation;
2. B404 protocol smoke;
3. B405 perturbation matrix;
4. **TX-AGE-DECOUPLING-v1 Stage A**;
5. Stage B only if triggered;
6. broader passive boundary-deviation hunt later;
7. reliability certification last.

## 14. Decision

The next discovery experiment should not be a passive fixed-tempo boundary hunt.

Use:

**FAST x4 + HOLD32 x12, F=16, b63, randomized blocks.**

If HOLD32 captures an unexplained specimen, use:

**HOLD8/HOLD32/HOLD56 x4 each**

to convert the rare event into a position-dependent Delta fingerprint.

This is the highest-information next step found by the current Monte Carlo sensitivity study.
