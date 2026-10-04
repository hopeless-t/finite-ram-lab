# FR-FP-035 — Hosted physical multi-state equal-capacity allocation

Status: **HOSTED PHYSICAL MULTI-STATE CANDIDATE**

Parent: **FR-FP-034**

## Question

Does the FR-FP-034 allocation matter physically when total resident capacity is
held exactly constant?

## Frozen physical fixture

Ten durable regular-file states:

    10 x 8 MiB

Shared WARM budget:

    5 states = 40 MiB

Sixty opportunities.

The synthetic reuse count for each state is proportional to the FR-FP-034
0..9 evidence-count ladder:

    [0,2,3,5,7,9,10,12,14,15]

Total restores:

    77

Reuse positions are deterministic from a frozen seed and identical between arms.

## Arms

### VALUE_RISK_ALLOCATOR

WARM:

    {5,6,7,8,9}

COLD:

    {0,1,2,3,4}

This is the qualified 40 MiB FR-FP-034 allocation.

### ANTI_VALUE_CONTROL

WARM:

    {0,1,2,3,4}

COLD:

    {5,6,7,8,9}

This uses exactly the same 40 MiB resident budget but places it on the opposite
end of the reuse/value ladder.

## Why no ALWAYS_WARM / ALWAYS_COLD arms

The current question is allocation quality under equal capacity.

WARM/COLD physical primitives were already hosted-qualified in FR-FP-030.

Repeating those extremes would add physical work without changing this decision.

This is a direct dogfood of the META-021 decision-relevance rule.

## Physical observations

At every opportunity:

- mincore residency for all ten files;
- total resident MiB;
- target-tier enforcement.

At every reuse:

- pre-restore residency;
- exact restore integrity;
- restore latency;
- process storage-read bytes when available.

## Qualification

Require:

- exact same 77-reuse schedule;
- exact same 40 MiB WARM capacity;
- byte-integrity PASS;
- WARM reuse physically resident;
- COLD reuse physically nonresident;
- value/risk arm: exactly 17 COLD restores;
- anti-value arm: exactly 60 COLD restores;
- same-capacity residency traces;
- lower COLD restore count for the qualified allocation;
- lower storage read volume when process accounting is available.

Latency superiority is observed but not used as a PASS gate because prior lanes
proved COLD latency nonstationary.

## North-Star consequence

This isolates the value of residency selection itself:

    same bytes resident
    different states resident
    different restore traffic

The Governor is now controlling not only how much memory is resident, but which
semantic state occupies the finite resident set.

## Claim ceiling

**HOSTED_PHYSICAL_TEN_STATE_EQUAL_SIZE_SAME_CAPACITY_ALLOCATION_ON_ONE_SYNTHETIC_REUSE_TRACE_ONLY**
