# FR-FP-058 — Compile the physical rent policy family

Status: **COMPILED POLICY LOOKUP CANDIDATE**

Parent: **FR-FP-057**

## Why

FR-FP-057 completes physical evidence for all eight decision-distinct policy
paths produced by the FP054 rent sweep.

The Governor should not keep solving the same knapsack when only external memory
rent changes.

The physical family is now frozen strongly enough to compile its scalar decision
boundary.

## Hot capsule

Only seven paths ever win under the explicit one-dimensional memory-rent
scalarization.

Keep hot:

    thresholds:
      0.073502
      0.158539
      0.184802
      0.187782
      0.211520
      0.324820

    paths:
      P0
      P2
      P3
      P4
      P5
      P6
      P7

Selection becomes one ordered lookup.

## Cold evidence

P1 is physically real and Pareto non-dominated in the typed three-axis surface,
but it never wins the memory-rent scalarization.

Therefore:

- P1 is excluded from the hot scalar lookup;
- P1 remains in the cold typed Pareto evidence;
- it can be rehydrated if a different external policy surface needs it.

## Qualification

Compare the compiled lookup against direct scoring of all eight hosted physical
paths at:

- 50,001 regular rent values from 0 to 0.5;
- every crossover exactly;
- both sides of every crossover;
- large-rent probes.

Require zero mismatches.

## Self-compression

The hot capsule must remain below 30% of the serialized full typed physical
evidence surface.

The limit is not relaxed if compilation fails.

## Invalidation

Rebuild the capsule if any of these change:

- physical policy-path evidence;
- semantic service values;
- physical actuation values;
- resident byte-time values.

External memory rent may change freely; that is the input the capsule was built
to route.

## North-Star consequence

The optimized structure becomes:

    rich physical evidence in cold storage
      -> exact compiled decision boundary in hot state
      -> O(log N) rent lookup
      -> no DP/knapsack while valid

## Claim ceiling

**COMPILED_LOOKUP_FOR_THE_EIGHT_FP057_HOSTED_PHYSICAL_POLICY_PATHS_ONLY**
