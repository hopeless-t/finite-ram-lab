# FR-FP-046 — Variable-size WARM budget knapsack

Status: **VARIABLE-SIZE SHADOW CANDIDATE**

Parent: **FR-FP-045**

## Why

FR-FP-034 through FR-FP-043 assumed every resident state occupied exactly
8 MiB.

That made the finite WARM allocator an equal-size slot problem.

Real semantic state, KV/cache objects and application working sets are not
equal size.

The first variable-size lane keeps the already-qualified FP34 semantic values
and deadline guards unchanged, and changes only physical size.

## Frozen heterogeneous sizes

State IDs 0..9 use:

    4, 6, 8, 10, 12, 14, 16, 8, 8, 12 MiB

Semantic values and deadline risks are reused from FR-FP-034.

Mandatory WARM remains:

    {7, 8, 9}

Their total physical size is:

    28 MiB

A byte budget below 28 MiB must fail closed before optimization.

## Why density fill is no longer guaranteed

For equal-size states, sorting by:

    expected penalty avoided / MiB

is equivalent to sorting by value.

For unequal 0/1 objects it becomes the classical density heuristic and is not
generally exact.

This lane therefore compares:

DENSITY_GREEDY
: take optional states in descending value/MiB order whenever they still fit.

DP_EXACT
: dynamic-programming 0/1 byte-budget allocator after mandatory bytes are
reserved.

EXHAUSTIVE
: enumerate every optional subset and use it only as the qualification oracle.

The scientific PASS gate does not require greedy to fail.

Greedy success/failure is an observed result.

## Budget sweep

Sweep:

    24, 28, 32, ... 96, 98 MiB

For every feasible byte budget require:

- mandatory states remain WARM;
- DP exact allocation matches exhaustive optimum;
- every COLD state satisfies the existing deadline tolerance;
- optimal expected COLD penalty never increases when byte capacity grows.

## Metrics remain separate

The allocator keeps separate:

- resident MiB;
- expected COLD restore penalty;
- deadline admissibility.

No hidden scalar utility is introduced.

## Next physical lane

If qualified:

1. create durable files with the actual heterogeneous sizes;
2. physically enforce the exact WARM byte set;
3. verify resident MiB against requested capacity;
4. compare exact placement with density-greedy under the same byte budget;
5. recalibrate promotion/eviction cost as a function of bytes instead of state
   count.

## Claim ceiling

**SYNTHETIC_VARIABLE_SIZE_ALLOCATION_USING_FP034_VALUES_AND_ONE_FROZEN_SIZE_VECTOR_ONLY**
