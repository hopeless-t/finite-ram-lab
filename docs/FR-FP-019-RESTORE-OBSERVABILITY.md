# FR-FP-019 — Restore observability plane

Status: **HOSTED PHYSICAL OBSERVABILITY CANDIDATE**

Parent: **FR-FP-018**

## Why

FR-FP-016 established large cross-run COLD restore nonstationarity.

FR-FP-017 found a heavy within-run COLD tail.

FR-FP-018 found significant order structure in both COLD and the WARM control.

That means a COLD-only hidden-state model is premature.

The next step is to expose runner / Linux I/O state around each restore.

## Paired physical trace

- state size: 8 MiB;
- 32 WARM/COLD paired blocks;
- alternating arm order;
- exact restore and mincore residency gates retained.

## Pre-restore observation window

After tier preparation and residency verification:

1. snapshot Linux/cgroup observables;
2. wait 20 ms without starting restore;
3. snapshot again;
4. perform restore;
5. snapshot immediately after restore.

The 20 ms delta is a candidate predictive state.

The restore-window delta is diagnostic only because it may be an effect of the
restore itself.

## Predeclared predictive features

COLD latency is tested against:

- global I/O PSI some delta;
- global I/O PSI full delta;
- cgroup I/O PSI some delta;
- cgroup io.stat read-byte delta;
- cgroup memory.current delta.

Each feature receives a 10,000-permutation Spearman test.

Familywise alpha is Bonferroni-corrected across the five predeclared features.

No predictive correlation is required for PASS.

A null result is a useful theory update.

## Restore-window diagnostics

Also record correlations between latency and:

- global/cgroup I/O PSI generated during restore;
- cgroup read bytes during restore;
- memory.current change during restore.

These may explain what physically happened, but they are not treated as
pre-restore predictors.

## Routing

If at least one pre-restore feature survives correction:

    PRE_RESTORE_OBSERVABLE_SIGNAL_CANDIDATE

Otherwise:

    CURRENT_PRE_RESTORE_OBSERVABLES_DO_NOT_EXPLAIN_COLD_LATENCY

The second route means the lab should broaden observability or adopt a
hierarchical uncertainty model rather than inventing a predictor from noise.

## Claim ceiling

**HOSTED_RESTORE_OBSERVABILITY_PILOT_ONLY**
