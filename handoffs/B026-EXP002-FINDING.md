# Bounce Handoff

> **Bounce ID:** B026  
> **Status:** COMPLETE

## Objective

Read EXP-002 with only the frozen primary, net-cost, and Red-Team analyses.

## Evidence

- run: `36228994342`;
- 20 runner blocks / 360 trials;
- primary CORRECT/NO_HINT ratio = 0.903x, exact p = 0.668;
- net interval ratio = 0.932x, exact p = 0.560;
- WRONG/CORRECT ratio = 35.64x, exact p = 1.91e-6.

## Frozen finding

Central-tendency benefit of correct semantic PAGEOUT versus NO_HINT is **not supported**.

Wrong semantic PAGEOUT is strongly and reproducibly harmful.

## Exploratory signal

P90 values were lower for CORRECT_PAGEOUT than NO_HINT, but no tail claim is authorized from EXP-002.

## Next recommended bounce

> Use EXP-002 only for exploratory tail characterization, then pre-register a new tail-risk hypothesis and design before collecting new evidence.

Do not retrofit a tail endpoint into EXP-002.

Any future coordination design must explicitly handle stale/wrong hints because the observed downside is large.

## Authority boundary

EXP-002 is neither a positive case for a coordinator nor a proof that semantic information lacks value.
