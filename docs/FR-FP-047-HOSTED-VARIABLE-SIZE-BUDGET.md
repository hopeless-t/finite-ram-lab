# FR-FP-047 — Hosted variable-size byte-budget allocation

Status: **HOSTED PHYSICAL VARIABLE-SIZE CANDIDATE**

Parent: **FR-FP-046**

## Why

FR-FP-046 proved that the equal-size allocator does not survive heterogeneous
state sizes.

The exact shadow solution becomes a mandatory-guarded byte-budget knapsack.

FR-FP-047 asks whether that exact byte placement can be physically realized on
hosted Linux.

## Frozen state sizes

MiB by state id:

    4, 6, 8, 10, 12, 14, 16, 8, 8, 12

Mandatory WARM remains:

    {7, 8, 9}

Mandatory bytes:

    28 MiB

## Budget schedule

Physically actuate:

    28 -> 40 -> 56 -> 72 -> 92 -> 44 MiB

Each phase recomputes the exact FR-FP-046 DP allocation.

Only the symmetric difference between the old and new WARM sets is actuated.

The target resident byte count is the allocator's actual used bytes, not the
budget ceiling, because heterogeneous sizes can leave unusable slack.

## Physical observation

Each state is a regular file of its frozen size.

WARM:
- fault/prefetch the full file into page cache.

COLD:
- fsync-compatible durable file remains;
- POSIX_FADV_DONTNEED removes clean page-cache residency.

For each phase measure:

- exact WARM state ids;
- weighted resident MiB from mincore residency fraction x state size;
- minimum WARM residency fraction;
- maximum COLD residency fraction;
- changed ids only;
- transition timing and promoted/evicted MiB.

## Fail-closed pressure

After the physical schedule, request:

    24 MiB

This is below the 28 MiB mandatory WARM floor.

Qualification requires:

- allocator returns infeasible;
- zero physical tier actions execute;
- the previous physical snapshot remains unchanged.

## Important boundary

Migration timing is recorded, but no bytes-to-time model is qualified here.

Variable-size migration cost is the next lane.

## Claim ceiling

**HOSTED_PHYSICAL_VARIABLE_SIZE_ALLOCATION_ON_ONE_TEN_STATE_SIZE_VECTOR_AND_BUDGET_SCHEDULE_ONLY**
