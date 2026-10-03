# FR-FP-019 Receipt

Status: **PASS / HOSTED RESTORE OBSERVABILITY PILOT QUALIFIED**

Parent: **FR-FP-018**

- workflow run: 37153426612
- job: 111291795608
- execution head: 516ddaa1202b136468d4aae131f21dc34251a4d2
- state size: 8 MiB
- paired blocks: 32
- pre-restore observation window: 20 ms
- permutation tests: 10,000 per predeclared feature

Physical tier separation:
- WARM files remained resident before restore
- COLD DONTNEED files remained nonresident before restore
- exact restore integrity: PASS
- WARM median restore: about 0.978 ms
- COLD median restore: about 3.845 ms

## Pre-restore predictive plane

Predeclared COLD predictors:
- global I/O PSI some delta
- global I/O PSI full delta
- cgroup I/O PSI some delta
- cgroup io.stat rbytes delta
- cgroup memory.current delta

Observed over the 20 ms pre-window:
- every feature was constant zero across all 32 COLD trials
- no Spearman coefficient is identifiable from a constant feature
- no predictive feature survives because there is no pre-restore variation to test

Route:

**CURRENT_PRE_RESTORE_OBSERVABLES_DO_NOT_EXPLAIN_COLD_LATENCY**

This is stronger than a weak nonsignificant correlation: the selected idle-window
observables exposed no varying precondition at all in this hosted fixture.

## Restore-window diagnostics

During COLD restore:
- every trial generated an 8,388,608-byte cgroup read
- WARM restore generated zero corresponding cgroup read bytes
- global/cgroup I/O PSI some vs COLD latency: Spearman rho about 0.793
- global/cgroup I/O PSI full vs COLD latency: Spearman rho about 0.792
- memory.current restore delta vs latency: rho about 0.230

Interpretation:

COLD latency is physically realized as storage read + I/O stall, and PSI dwell
tracks the realized restore cost strongly.

But the tested 20 ms idle-window PSI/io/memory counters do not predict that cost
before restore begins.

Do not train a predictor from restore-window PSI: it is diagnostic and may be a
consequence of the restore itself.

Decision:

**SEPARATE_PRE_RESTORE_PREDICTIVE_SIGNALS_FROM_RESTORE_WINDOW_STALL_DIAGNOSTICS**

Next:

Exploit already-existing independent GitHub-hosted CI runs as a zero-new-run
cross-run dataset. Estimate the run-level distribution of COLD restore regimes
with WARM control before adding wider predictive telemetry.

Claim ceiling:

**HOSTED_RESTORE_OBSERVABILITY_PILOT_ONLY**
