# FR-FP-020 — Cross-run restore uncertainty prior

Status: **REUSED EVIDENCE ANALYSIS CANDIDATE**

Parent: **FR-FP-019**

## Why

FR-FP-019 found no varying predictive signal in the tested 20 ms idle window.

At the same time, every downstream CI execution already reruns the physical
FR-FP-016 4/8/16 MiB restore probe on a fresh GitHub-hosted runner.

Those runs are free evidence.

FR-FP-020 reuses them rather than scheduling another physical campaign.

## Frozen dataset

Fifteen existing CI runs are included.

Every included run satisfies:

- exact prepare/restore integrity;
- WARM pre-residency;
- COLD DONTNEED nonresidency;
- COLD slower than WARM at every tested size.

No new hosted runner is requested by this lane.

Primary cross-run variable:

    8 MiB COLD median restore latency

WARM 8 MiB median is retained as control.

## Why one median is unsafe

The observed COLD run medians span multiple tens of times from minimum to
maximum.

Some fresh runners show a few-millisecond regime.

Others show approximately 0.1-second 8 MiB restore.

The same code can be internally near-linear with state size while living in a
completely different bandwidth regime.

Therefore:

    one universal restore latency
    or
    one universal restore bandwidth

is not an adequate Governor input.

## Uncertainty representation

FR-FP-020 freezes:

- empirical run-level quantiles;
- empirical deadline-miss rates;
- 20,000-bootstrap 95% intervals for the median and deadline-miss rates;
- COLD vs WARM log-dispersion;
- the largest adjacent gap in sorted log COLD latency.

The largest gap is recorded only as a discrete-regime candidate.

It is not sufficient to declare a stable mixture model with fifteen runs.

## Governor consequence

Until current-run calibration exists, the Governor should carry a prior such as:

    P(restore latency > deadline)

rather than a single expected restore time.

When a few current-run restore observations become available, a later lane can
test online posterior / calibration updates against this cross-run prior.

## Self-improvement consequence

This lane uses zero new physical runs.

It converts routine downstream qualification work into reusable evidence.

That is the same Finite RAM principle at the experiment layer:

    do not recompute information that already exists durably.

## Claim ceiling

**FIFTEEN_REUSED_GITHUB_HOSTED_CI_RUNS_FOR_8MIB_RESTORE_ONLY**
