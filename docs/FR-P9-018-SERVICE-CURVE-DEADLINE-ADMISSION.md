# FR-P9-018 — ServiceCurve deadline admission

## Why this exists

FR-P9-017 physically qualified a narrow hosted proxy where equal total CPU-service opportunity was not deadline-equivalent when the service arrived at different times. FR-P9-018 does **not** generalize that physical result into a scheduler theorem. Instead it asks a smaller analytic question: given a declared cumulative service curve for one resource, what is the minimum fail-closed admission rule for a bounded deadline-sensitive reconstruction?

This is an **analytic/synthetic evidence class**. FR-P9-017 remains the physical anchor and is not replaced by this proof.

## Contract

```text
ServiceCurveSnapshot = (
    resource_kind,
    contention_domain,
    measurement_epoch,
    samples[(time, cumulative_delivered_service)]
)

ServiceDemand = (
    work_id,
    resource_kind,
    contention_domain,
    deadline,
    required_service
)
```

Service units are **resource-specific**. CPU service, transfer bytes, device queue service and memory migration work are not silently scalarized into one unit.

For a current curve epoch:

```text
ADMIT_RESOURCE_FEASIBLE
    iff
ServiceCurve(deadline) >= RequiredService
```

If the resource identity or contention domain differs, admission fails closed. If the service-curve epoch is stale, the result is `REPLAN_REQUIRED`; stale evidence can never become an admission grant.

## Frozen analytic qualification

The implementation performs four independent checks.

1. **Exhaustive oracle equivalence**
   - four discrete time bins;
   - each bin contributes 0..3 service units;
   - every deadline 1..4;
   - every requirement 0..13;
   - operator result compared with direct cumulative-sum truth.

2. **Equal-total timing adversary**
   - front curve `(4,4,0,0)`;
   - back curve `(0,0,4,4)`;
   - same horizon total, deadline at bin 2, demand 6;
   - front must admit while back must reject.

3. **Stale-epoch adversary**
   - forecast is front-loaded at epoch 10;
   - actual is back-loaded at epoch 11;
   - same horizon total;
   - naive forecast admission says ADMIT;
   - epoch-aware use of the stale forecast must say `REPLAN_REQUIRED`;
   - current actual curve says insufficient service before deadline.

4. **Deterministic Monte Carlo**
   - forecast and actual have the same total service but random temporal placement;
   - the forecast epoch is always stale relative to actual observation;
   - measure naive false-admits and epoch-guarded false-admits.

The expected safety property is not that forecasts are accurate. It is that stale forecasts are never silently converted into execution feasibility.

## Boundary with authority

```text
Resource feasibility != execution authority
Replan request       != retry permission
Placement candidate  != invocation
```

`ADMIT_RESOURCE_FEASIBLE` means only that the bounded resource contract is feasible under the current declared service curve. An authority layer must still independently permit execution.

## Relation to external prior art

External scheduler/tiering work is tracked separately in `FR-META-EXT-001` and Curiosity Intake. Those systems motivate vocabulary and falsifiers but their benchmark claims are not local evidence.

Particularly relevant dimensions are:
- sched_ext/scx: replaceable CPU scheduling policy and fail-safe fallback;
- DAMON/DAMOS: observation plus time/byte quotas and prioritization;
- TierBPF: migration admission separated from candidate page placement;
- Equilibria/xTier: observability, fairness, phase adaptation and control-loop invalidation.

## Next physical gate

`FR-P9-019` should make the service curve itself a forecast that can become stale during execution preparation:

```text
forecast ServiceCurve(epoch=e0)
        ↓ plan says feasible
resource condition changes
        ↓ observe epoch=e1
execution admission must stop
        ↓ REPLAN_REQUIRED
current ServiceCurve(e1)
        ↓ recompute feasibility
```

The target physical claim is only that stale resource evidence can be detected and forced through a replan path without widening authority.

Claim ceiling:
`ANALYTIC_DISCRETE_SERVICE_CURVE_ADMISSION_ONLY_NO_PHYSICAL_SCHEDULER_OR_APPLICATION_CLAIM`
