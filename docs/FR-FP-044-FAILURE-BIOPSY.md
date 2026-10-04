# FR-FP-044 Failure Biopsy — non-standard Infinity marker

Status: **EVIDENCE-SURFACE REPAIR / SCIENTIFIC RESULT UNCHANGED**

Initial workflow:
- 37216190316
- job: 111477068774
- head: f6ca7ee30b5c92232277267c9ebf94c56b4d8508

Scientific result:
- PASS
- 7,564 interval comparisons
- 0 mismatches

Observed evidence-surface defect:

Python emitted:

    Infinity

for the break-even horizon of a context where the candidate WARM set was
identical to the current WARM set.

Python's JSON encoder accepts this extension, but strict JSON consumers do not.

## Repair

Replace non-finite sentinel values with:

    break_even_horizon_rounds = null
    break_even_reason = "NO_PLACEMENT_CHANGE"

or, for a real value-free move:

    break_even_reason = "NO_POSITIVE_SERVICE_BENEFIT"

Finite break-even thresholds are unchanged.

## Scientific contract

Unchanged:
- migration cost model;
- semantic benefit;
- horizon interval gate;
- endpoint equivalence grid;
- safety override;
- qualification thresholds.

## Compiled lesson

**A reusable research receipt must satisfy strict portable serialization, not
only the producer language's permissive encoder.**

Claim ceiling:

**FP044_PORTABLE_JSON_EVIDENCE_SURFACE_REPAIR_ONLY**
