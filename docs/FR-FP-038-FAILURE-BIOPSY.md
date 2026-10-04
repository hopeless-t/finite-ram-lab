# FR-FP-038 Failure Biopsy — Fixture Richness Was Mistaken for a Law

Status: **TEST-CONTRACT REPAIR / SCIENTIFIC DATA UNCHANGED**

Failed workflow:
- run: 37209632711
- job: 111457983281
- head: c406585efa350eb0c3175632c8191e6c665ef071

Observed result:
- exhaustive optimum agreement: PASS
- five-slot capacity preservation: PASS
- deadline-risk guard: PASS
- zero-action evidence phase: PASS
- minimal-delta actuation vs full re-enforcement: PASS
- online allocation vs phase-1 static placement: PASS
- distinct optimal WARM sets observed: 2

Failed gate:

    unique_warm_sets >= 3

## Root cause

"At least three different optimal sets" was not derived from the research law.

The actual hypothesis is only:

> new reuse evidence can change the optimal placement, and when it does not,
> no actuation should occur.

That requires at least two distinct optimal sets, not three.

Forcing the evidence schedule to create a third set would tune the fixture to a
desired-looking outcome.

## Repair

Change only the qualification gate:

    unique_warm_sets >= 2

Do not change:
- the reuse evidence schedule;
- state values;
- allocator;
- deadline guard;
- static comparator;
- exhaustive oracle;
- zero-action requirement.

## Meta lesson

**DO_NOT_PROMOTE_A_DESIRED_DEGREE_OF_VISUAL_OR_BEHAVIORAL_RICHNESS_INTO_A
SCIENTIFIC_PASS_GATE_UNLESS_THE_THEORY_REQUIRES_IT.**

Claim ceiling:

**FR_FP_038_FIXTURE_RICHNESS_GATE_REPAIR_ONLY**
