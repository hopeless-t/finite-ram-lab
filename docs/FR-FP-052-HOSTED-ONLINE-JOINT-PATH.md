# FR-FP-052 — Hosted physical online joint path

Status: **HOSTED PHYSICAL ONLINE-JOINT CANDIDATE**

Parent: **FR-FP-051**

## Why

FR-FP-051 showed in shadow evaluation that the correct control problem is not:

    compute semantic optimum
    then decide whether to migrate

but:

    choose the admissible placement that minimizes
    service cost + physical migration cost

across all placements.

FR-FP-052 tests the resulting five-phase path on real hosted page-cache
actuation.

## Two physical arms

Use the same ten heterogeneous states and the same capacity schedule:

    40 -> 28 -> 72 -> 44 -> 56 MiB

### JOINT

Follow the FR-FP-051 migration-aware optimal path.

### MIGRATION-BLIND SEMANTIC

At every phase, jump directly to the instantaneous semantic optimum.

Both begin from the same phase-1 placement.

## Physical measurement

For each transition:

- actuate only the old/new symmetric difference;
- use the size-explicit qualified actuator;
- measure physical transition time;
- verify WARM residency;
- verify COLD nonresidency;
- verify resident MiB against the target placement.

Initial placement cost is excluded for both arms because it is identical.

## Hybrid total

Per-phase service cost remains the qualified expected-penalty model.

Migration is replaced by hosted observed actuation time:

    physical hybrid total
      =
    modeled service cost
      +
    hosted physical migration time

The critical test is whether the FR-FP-051 advantage survives that physical
substitution.

## Claim ceiling

**HOSTED_PHYSICAL_FIVE_PHASE_VARIABLE_SIZE_JOINT_PATH_ON_ONE_FROZEN_ONLINE_TRACE_ONLY**
