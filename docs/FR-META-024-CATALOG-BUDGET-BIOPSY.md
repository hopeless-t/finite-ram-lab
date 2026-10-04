# FR-META-024 Catalog Budget Biopsy

Status: **META-COMPRESSION REPAIR CANDIDATE**

Failed workflow:
- run: 37218911680
- catalog fraction: 0.3006832405121433
- frozen limit: < 0.30

All information-value pruning behavior tests passed.

The only failing contract was the resident catalog budget.

## Repair sequence

Already compiled before the failed run:

    mc = SKIP

as an implicit default.

The catalog still exceeded the frozen limit by ~0.068 percentage points.

Second compression:

    maturity = QUALIFIED

becomes an implicit resident default.

Exceptional maturity states remain explicit:

- STABLE
- STABLE_GUARD
- QUALIFIED_GUARD
- QUALIFIED_NEGATIVE

The emitted decision capsule still restores an explicit maturity value.

## Invariant

Do not relax the budget to admit a new skill.

Compress repeated executable metadata first.

Claim ceiling:

**META024_RESIDENT_CATALOG_DEFAULT_VALUE_COMPRESSION_ONLY**
