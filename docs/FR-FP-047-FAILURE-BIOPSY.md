# FR-FP-047 Failure Biopsy — hidden equal-size prefetch primitive

Status: **IMPLEMENTATION CONTRACT FAILURE / ALLOCATOR THEORY UNCHANGED**

Failed workflow:
- run: 37218563694
- job: 111484034114
- head: 31c89e4a3464120aa787c3999d71eb95b3e577f7

Observed exception:

    RuntimeError: unexpected_prefetch_eof

## Root cause

The first hosted variable-size implementation reused the FR-FP-030 WARM-tier
actuator.

That actuator calls a helper whose read target is the parent fixture's global:

    SIZE_BYTES = 8 MiB

FR-FP-047 contains physical files smaller than 8 MiB.

A 4 MiB or 6 MiB state promoted through the inherited helper therefore tried to
prefetch bytes beyond EOF.

The failure happened before the variable-size allocation hypothesis could be
qualified.

## Repair

Keep the parent primitive unchanged for its already-qualified 8 MiB contract.

FR-FP-047 now carries a size-explicit actuator:

    _warm_file_sized(path, size_bytes=...)
    _enforce_tier_sized(path, tier=..., size_bytes=...)

Every state passes its own frozen file size.

Unchanged scientific contract:

- same state-size vector;
- same exact DP allocator;
- same byte-budget schedule;
- same mincore thresholds;
- same mandatory 28 MiB floor;
- same fail-closed 24 MiB request.

## Theory update

A reusable physical primitive is not size-generic merely because its API omits
size.

Hidden fixture constants are part of the primitive contract.

Compiled lesson:

**BEFORE_REUSING_A_PHYSICAL_PRIMITIVE_ACROSS_A_NEW_GEOMETRY_EXPOSE_AND_BIND_ALL_HIDDEN_FIXTURE_DIMENSIONS.**

Claim ceiling:

**FP047_SIZE_BINDING_IMPLEMENTATION_BIOPSY_ONLY**
