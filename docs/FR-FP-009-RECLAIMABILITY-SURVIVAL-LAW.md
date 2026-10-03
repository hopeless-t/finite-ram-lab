# FR-FP-009 — Reclaimability survival law

Status: **ANALYTIC LAW CANDIDATE**

Parent: **FR-FP-008**

## From two variables to one distribution

FR-FP-007 and FR-FP-008 showed that the Governor needs both:

- whether safe reclaimability occurs;
- when it occurs.

Those are naturally two aspects of a time-to-event distribution.

Define:

    T = first safe-reclaimability step

Trajectories with no safe event inside the observation horizon remain
right-censored.

Define the empirical survival function:

    S_T(t) = P(T > t)

with censored never-safe trajectories remaining in the surviving mass.

## Frozen transfer model

The analytic result applies only under these assumptions:

- one new hot state arrives per step;
- always-preemptive transfer;
- at most one new transfer is initiated per step;
- fixed integer transfer lead L;
- each completion removes one hot state;
- safe reclaimability collapses retained hot history to one state;
- no transfer failure.

Under this model, the initial transfer pipeline has a simple boundary.

### Case 1 — B > L

The hot budget B is larger than transfer lead L.

The first completion arrives before the hot set can overflow, and the pipeline
then keeps pace with one new state per step.

Therefore:

    P(semantic OOM) = 0

even if no safe endpoint appears inside the horizon.

### Case 2 — B <= L

The hot set reaches the budget before the first transfer can complete.

The only way to avoid semantic OOM is for safe reclaimability to arrive by the
budget deadline.

Therefore:

    P(semantic OOM) = P(T > B)
                    = S_T(B)

This single survival term includes both:

- late-but-eventually-safe trajectories;
- never-safe / right-censored trajectories.

## Exact validation

The law is checked against the step simulator across:

- transfer lead 1..6;
- hot budgets 2,3,4,5,6,8,10;
- safe-event shifts 0,2,4,6,8,10.

Total:

    252 cells

The qualification contract requires:

    max absolute error = 0

not merely approximate agreement.

## Why this matters for research speed

FR-FP-004 needed Monte Carlo to discover the phase geometry because the law was
not yet known.

Once the law is frozen under explicit assumptions, repeating the full simulator
for the same decision becomes redundant.

The compiled routing rule can be:

    if assumptions hold:
        use survival law
        Monte Carlo = SKIP
    else:
        invalidate the skill
        return to simulation / experiment

This is exactly the Finite RAM pattern applied to reasoning:

    expensive history / simulation
      -> qualified sufficient statistic
      -> small resident law

## Invalidation

The law must be invalidated if any frozen mechanism changes, including:

- state arrival rate;
- transfer throughput;
- variable or stochastic transfer lead;
- transfer failures;
- safe reclaimability not collapsing hot history;
- multiple state sizes / transfer service times.

Those are future research lanes, not reasons to silently stretch the law.

## North-Star consequence

The Governor's predictive state can now be expressed as:

    transfer geometry (B, L)
    +
    reclaimability survival S_T(t)

rather than an ad-hoc pair of coverage and ETA scalars.

A future empirical workload can estimate a survival / hazard model from real
reclaimability events and censoring, then use the same routing structure.

## Claim ceiling

**ANALYTIC_LAW_FOR_FROZEN_SYNTHETIC_TRANSFER_MODEL_ONLY**
