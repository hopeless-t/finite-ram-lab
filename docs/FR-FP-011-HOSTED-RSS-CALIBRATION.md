# FR-FP-011 — Hosted live-state to RSS calibration

Status: **HOSTED PHYSICAL CALIBRATION CANDIDATE**

Parent: **FR-FP-010**

## Question

FR-FP-010 produced one striking hosted physical point:

    6 live x 8 MiB
    -> 48 MiB RSS peak

and:

    12 live x 8 MiB
    -> 96 MiB RSS peak

FR-FP-011 tests whether that relation is a reusable calibration curve rather
than a two-point coincidence.

## Sweep

State size remains frozen at:

    8 MiB

Trajectory length remains:

    12 states

Synthetic semantic safe frontier is swept across:

    2, 4, 6, 8, 10, 12 live states

Every state is an anonymous private mmap and every OS page is touched.

At the safe frontier, old mappings are physically closed.

## Physical fits

Two regressions are computed:

    logical peak KiB -> VmRSS peak delta KiB

and:

    logical peak KiB -> RssAnon peak delta KiB

The qualification requires:

- R² > 0.999;
- slope between 0.90 and 1.10;
- VmRSS maximum absolute residual < 4 MiB;
- every gated arm ends at one live state.

These tolerances are intentionally wider than the exact FR-FP-010 result
because hosted physical observations may contain system noise.

## Why this matters

The predictive Governor operates in semantic units such as:

    live trajectory states

The operating system enforces resource limits in byte units.

A calibrated conversion:

    live semantic state count
      -> resident bytes

is therefore required before semantic pressure prediction can drive a physical
budget.

If the fit passes, the frozen mmap fixture supports a simple hosted estimator:

    resident trajectory bytes
    ~= live states x calibrated bytes/state

This is not yet a universal estimator.

## Self-improvement note

FR-FP-010 initially passed without printing its physical result and required a
second CI run to recover the values.

FR-FP-011 emits its result marker on the first qualification run.

The observation protocol has therefore incorporated its own failure biopsy.

## Claim ceiling

**HOSTED_LINUX_ANONYMOUS_MMAP_LIVE_STATE_RSS_CALIBRATION_ONLY**
