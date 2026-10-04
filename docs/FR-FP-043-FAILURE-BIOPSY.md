# FR-FP-043 Failure Biopsy — result serialization

Status: **IMPLEMENTATION FAILURE / SCIENTIFIC CONTRACT UNCHANGED**

Failed workflow:
- 37215695610
- job: 111475623878
- head: 181e2ede5d6c04713c67e57271866b139841ca87

Observed exception:

    TypeError: Object of type set is not JSON serializable

Location:

    test setUpClass
      -> run_panel()
      -> FR_FP_043_RESULT json.dumps(...)

## Root cause

The physical experiment completed far enough to return its result object, but
the public result retained Python set objects inside:

    hysteresis_plan.targets

The test marker requires a JSON-safe durable receipt surface.

## Repair

Normalize only the public result representation:

    set[int] -> sorted list[int]

Internal set semantics used for allocation and actuation remain unchanged.

Frozen scientific conditions remain unchanged:

- 100-round phase horizon;
- ten 8 MiB states;
- five WARM slots;
- immediate semantic-optimum arm;
- hysteretic arm;
- physical page-cache actuation;
- service cost and observed migration cost kept separate;
- mixed HOLD/MIGRATE gate unchanged.

## Compiled lesson

**A physical experiment is not durably qualified until its result surface is
serializable and replayable.**

Claim ceiling:

**FP043_RESULT_SERIALIZATION_BIOPSY_ONLY**
