# FR-FP-008 — Reclaimability coverage × timing frontier

Status: **SYNTHETIC INTERACTION CANDIDATE**

Parent: **FR-FP-007**

## Question

FR-FP-007 separated two failure domains:

- timing gap;
- coverage gap.

FR-FP-008 asks whether repairing either one independently is enough to cross the
lead4 / budget4 deadline frontier.

## Synthetic application-quality lever

The experiment scales every trajectory value by a uniform factor.

This scales both:

- endpoint gap;
- local residual.

It is a toy proxy for an application/model that forms a higher-quality endpoint
representation more quickly.

It is not a claim that any real model, quantizer, distillation method, or
representation can achieve the frozen scale factors.

## Grid

Quality scale:

    1.00, 0.40, 0.30, 0.25, 0.20, 0.18, 0.17, 0.16

Safe-event timing shift:

    0, 2, 4, 6, 8, 10 steps earlier

The transfer geometry remains:

- lead = 4;
- hot budget = 4;
- always-preemptive transfer.

## Three critical cells

### Timing only

Quality scale stays 1.00.

Safe events are shifted ten steps earlier.

Result:

    semantic OOM = 19.4%

The system hits the never-safe coverage floor.

### Coverage only

Quality scale 0.16 is the first frozen grid point with 100% safe-endpoint
coverage.

No timing shift is applied.

Result:

    coverage = 100%
    semantic OOM remains above 30%

Therefore turning every trajectory into an eventually safe trajectory does not
make the endpoint arrive soon enough.

### Joint repair

Quality scale:

    0.16

Timing shift:

    8 steps

Result:

    coverage = 100%
    semantic OOM = 0%

The frozen deadline frontier is crossed only when coverage and timing are
repaired together.

## Governor consequence

The Governor must not collapse reclaimability into one scalar ETA.

It needs at least two quantities:

    P(safe reclaimability occurs within the task horizon)

and, conditional on safe reclaimability:

    ETA(safe reclaimability)

These may later become a survival / hazard formulation rather than two manually
separate numbers.

## Research consequence

Application-side endpoint quality and system-side transfer geometry are coupled.

A better application representation can improve coverage but still miss the
deadline.

A faster scheduler can exploit early endpoints but cannot create endpoints that
never become safe.

The next mathematical layer should therefore model reclaimability as a
time-to-event distribution with censoring for never-safe trajectories.

## Claim ceiling

**SYNTHETIC_COVERAGE_TIMING_INTERACTION_ONLY**
