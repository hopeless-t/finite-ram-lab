# FR-META-020 Catalog Budget Biopsy

Status: **META-COMPRESSION REPAIR CANDIDATE**

Failed workflow:
- 37195539681
- head: 476c97e9eb7b42ed6495b21ddaa82a9724ca3ba3

Observed:
- new decision-relevance skill behavior: PASS
- catalog budget: FAIL
- catalog fraction: 0.320319
- frozen limit: <0.30

## Root cause

The new useful skill was added to a catalog that already carried metadata not
used by executable selection.

Repeated resident fields:

- kind
- replications

These fields do not affect trigger matching, priority, capsule emission,
invalidation, or primary action.

## Repair

Evict those two non-decision metadata fields from the executable resident
catalog.

Keep:

- trigger predicates;
- priority;
- action;
- MC disposition;
- evidence PRs;
- maturity;
- invalidation contract.

## Compiled lesson

**WHEN_A_COMPILED_SKILL_CAUSES_A_RESIDENT_BUDGET_FAILURE, EVICT
DECISION-IRRELEVANT_METADATA_BEFORE_RELAXING_THE_BUDGET.**

Claim ceiling:

**META020_EXECUTABLE_CATALOG_METADATA_COMPRESSION_ONLY**
