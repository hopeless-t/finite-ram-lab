# FR-META-019 Failure Biopsy — Skill catalog exceeded resident budget

Status: **META-COMPRESSION FAILURE / CONTRACT PRESERVED**

Failed workflow:
- 37191536269
- head: 08545e43b7a202df3111baed1d67797fb6a0345d

Observed:
- every new decision-routing test passed;
- catalog compression gate failed;
- catalog fraction of source history: 0.32824;
- frozen limit: <0.30.

## Rejected repairs

Do not:
- relax the 30% limit merely to make CI green;
- inflate SOURCE_HISTORY_CHARACTERS;
- remove evidence/invalidation semantics.

Those would hide resident-context growth instead of reducing it.

## Compression repair

The first implementation represented:

- one-probe calibration;
- optional two-probe lower-envelope precision;

as two separate skills.

They share the same evidence scope and the same baseline/tail separation.

Compile them into one capsule:

    COLD_RESTORE_CALIBRATION_FRONTIER

with action:

    ONE_PROBE_BASELINE
      -> OPTIONAL TWO_PROBE MIN IF WORTH COST
      -> KEEP TAIL PRIOR

The value-of-information decision remains external and does not require a second
resident rule.

The negative-result CI-repair guard remains separate because it is an
independent meta invariant.

## Compiled lesson

**WHEN_THE_SKILL_CATALOG_HITS_ITS_OWN_RESIDENT_BUDGET, COMPRESS OVERLAPPING
DECISIONS BEFORE EXPANDING THE BUDGET.**

Claim ceiling:

**SKILL_CATALOG_RESIDENT_BUDGET_BIOPSY_ONLY**
