# FR-FP-009 Receipt

Status: **PASS / ANALYTIC RECLAIMABILITY SURVIVAL LAW QUALIFIED**

Parent: **FR-FP-008**

- workflow run: 37143792135
- job: 111263487685
- execution head: ddbf95b83b96f1d7f7706d02df587d1ace368159
- comparison cells: 252
- max absolute analytic-vs-simulation error: 0.0

Frozen analytic law:

For hot budget B and fixed transfer lead L under the frozen toy assumptions:

    if B > L:
        P(semantic OOM) = 0
    else:
        P(semantic OOM) = S_T(B)

where T is first safe-reclaimability time and S_T is its empirical survival
function. Never-safe trajectories remain right-censored beyond the observation
horizon.

The law exactly matches the step simulator across:

- transfer lead 1..6;
- hot budgets 2,3,4,5,6,8,10;
- safe-event shifts 0,2,4,6,8,10.

Interpretation:

The earlier separate coverage and timing variables collapse into one censored
time-to-event distribution.

This law replaces repeated Monte Carlo only while all frozen transfer-model
assumptions remain true.

Decision:

**USE_SURVIVAL_LAW_INSTEAD_OF_MONTE_CARLO_WHEN_THE_FROZEN_TRANSFER_ASSUMPTIONS_HOLD**

Compiled skill candidate:

**SEMANTIC_OOM_SURVIVAL_LAW / MC=SKIP**

Claim ceiling:

**ANALYTIC_LAW_FOR_FROZEN_SYNTHETIC_TRANSFER_MODEL_ONLY**
