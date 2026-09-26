# ENV-005 Initial Finding

> **Status:** INEFFECTIVE FOR THIS WORKLOAD  
> **Run:** 36228386627

## Question

Does `MADV_COLD` measurably bias which of two equal anonymous regions loses residency during the 164 MiB transition-zone pressure workload?

## Execution

All frozen execution checks passed:

- 8 independent runner blocks;
- 16 total trials;
- target identity A/B balanced in every block;
- all `MADV_COLD` calls succeeded;
- all content-integrity checks passed;
- no OOM events.

## Result

After the 96 MiB burst:

    median cold-hinted target residency = 1.000
    median matched control residency    = 1.000
    median target - control difference = 0.000

Exact block-level sign-flip result:

    observed mean target-control difference = +0.1396
    exact two-sided p = 0.125

Observed trial differences ranged from:

    0.000 to +0.5853

Median cgroup swap growth was about 7.45 MiB.

## Classification

    INEFFECTIVE

The pre-registered direction was negative: the hinted target should have become less resident than its matched control.

That pattern was not observed.

In some trials the target was instead **more** resident than the control.

## Interpretation

`MADV_COLD` is supported by the hosted kernel, but the hint was not strong or reliable enough to steer semantic-region residency in this transition-zone workload.

This is consistent with the interface being advisory: it makes pages more probable reclaim targets rather than guaranteeing their eviction.

## Research consequence

Do not spend a full performance experiment on `MADV_COLD` under the current workload.

The escalation order permits testing the next existing userspace mechanism before inventing a coordinator.

The next candidate is the stronger existing `MADV_PAGEOUT` operation, used on the not-soon-needed region **before natural pressure**, without explicit cgroup proactive reclaim.

## Authority boundary

ENV-005 does not show that `MADV_COLD` is useless generally.

It shows only that it did not provide a usable region-selective residency bias under this hosted workload and frozen probe.
