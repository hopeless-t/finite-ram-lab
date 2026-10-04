# FR-FP-035 Receipt

Status: **PASS / HOSTED PHYSICAL EQUAL-CAPACITY MULTI-STATE ALLOCATION QUALIFIED**

Parent: **FR-FP-034**

- workflow run: 37204886772
- state count: 10
- state size: 8 MiB
- WARM capacity: 5 states = 40 MiB
- opportunities: 60
- total reuse events: 77
- new physical hosted run: yes

Both arms used exactly the same:
- 10 durable 8 MiB states;
- 40 MiB WARM capacity;
- reuse schedule;
- total restore count.

Physical residency:
- VALUE/RISK mean resident: 40 MiB
- ANTI-VALUE mean resident: 40 MiB
- VALUE/RISK residency integral: 2400 MiB-opportunity
- ANTI-VALUE residency integral: 2400 MiB-opportunity
- post-enforcement min/max: exactly 40 MiB in both arms

## Qualified value/risk allocation

WARM:

    {5,6,7,8,9}

COLD:

    {0,1,2,3,4}

Observed:
- WARM restores: 60
- COLD restores: 17
- storage reads: 142,606,336 bytes = 136 MiB
- total restore latency: 118.291 ms
- COLD median restore: 3.741 ms
- WARM median restore: 0.920 ms
- 10 ms COLD deadline misses: 0

## Equal-capacity anti-value control

WARM:

    {0,1,2,3,4}

COLD:

    {5,6,7,8,9}

Observed:
- WARM restores: 17
- COLD restores: 60
- storage reads: 503,316,480 bytes = 480 MiB
- total restore latency: 255.890 ms
- COLD median restore: 3.866 ms
- WARM median restore: 1.008 ms
- 10 ms COLD deadline misses: 0

## Same-capacity effect

Compared with the anti-value control:

- COLD restore count: 71.67% lower
- storage read volume: 71.67% lower
- observed total restore latency: 53.77% lower

Every restore passed exact byte-integrity verification.

The latency reduction is reported as an observation, not a universal guarantee.

Decision:

**ALLOCATE_EQUAL_RESIDENT_BYTES_TO_THE_STATES_WITH_HIGHEST_CONSERVATIVE_AVOIDED_COLD_COST_SUBJECT_TO_DEADLINE_GUARDS**

Theory update:

Resident-byte quantity alone is insufficient.

At exactly equal 40 MiB residency, semantic placement choice changed physical
restore traffic by more than 3.5x.

Thus the Governor objective must optimize:

    which state is resident

not merely:

    how many bytes are resident

Next:

Make the WARM budget time-varying and qualify minimal-migration online
reallocation across pressure transitions.

Claim ceiling:

**HOSTED_PHYSICAL_TEN_STATE_EQUAL_SIZE_SAME_CAPACITY_ALLOCATION_ON_ONE_SYNTHETIC_REUSE_TRACE_ONLY**
