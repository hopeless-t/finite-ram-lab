# FR-FP-058 Receipt

Status: **PASS / EXACT COMPILED PHYSICAL RENT LOOKUP QUALIFIED**

Parent: **FR-FP-057**

Final qualification:
- workflow run: 37227148128
- job: 111509058862
- execution head: 616d2b6a933460b5b6036b78ed9c9f878c096d11
- direct validation points: 50,020
- mismatches: 0

## Compiled hot capsule

Thresholds:
- 0.07350214904258025
- 0.1585393108400696
- 0.1848015299439954
- 0.18778152413473126
- 0.2115197524954894
- 0.32482048730057045

Supported paths:
- P0
- P2
- P3
- P4
- P5
- P6
- P7

P1 remains in cold typed Pareto evidence because it is physically non-dominated
but never wins the one-dimensional explicit memory-rent scalarization.

Resident representation:
- full typed physical evidence: 1762 serialized chars
- compiled capsule: 340 chars
- hot fraction: 0.192963

## Numerical boundary contract

The first two qualification attempts exposed floating-point crossover semantics.

No physical crossover was moved.

Final canonical equivalence rule:

    tie_tolerance
      =
    64 * machine_epsilon * max_abs_score

Within a numerical tie:
1. choose lower resident MiB-round;
2. then stable path ID.

This absorbs only floating representation residue and does not merge
1e-12-rent-neighbor decisions.

## Decision

**USE_COMPILED_RENT_INTERVAL_LOOKUP_AND_SKIP_DP_KNAPSACK_WHILE_THE_QUALIFIED_PHYSICAL_POLICY_FAMILY_IS_VALID**

Invalidation:
- physical policy-path evidence changes;
- semantic service values change;
- physical actuation values change;
- resident byte-time values change.

External memory rent may change freely.

Meta consequence:

Keep the decision boundary hot.
Keep the richer physical evidence and solver cold.
Rehydrate the rich surface only when the compiled family's validity contract
breaks.

Claim ceiling:

**COMPILED_LOOKUP_FOR_THE_EIGHT_FP057_HOSTED_PHYSICAL_POLICY_PATHS_ONLY**
