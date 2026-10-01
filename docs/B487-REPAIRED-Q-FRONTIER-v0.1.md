# B487 — Repaired q Frontier v0.1

Status: **FULL NUMERICAL OLD-vs-REPAIRED FRONTIER REQUALIFICATION**.

## 1. Why the old Governor cannot simply inherit B486

B486 qualified the centering repair only as an isolated primitive.

The existing q frontier and Governor were calibrated with the old boolean-index
centering.

Therefore the repaired runtime must rebuild the full numerical operating surface.

## 2. Paired conditions

Eight conditions are frozen:

```text
BOOLEAN_INDEX x q={1,2,4,7}
TILED_WHERE   x q={1,2,4,7}
```

All use the same deterministic workload seed as B469:

`seed=469`.

## 3. Runner-block balance

Eight independent hosted-runner jobs.

Each job executes all eight conditions once in fresh child processes.

The condition list is cyclically rotated by block ID, so every condition occupies
every execution position exactly once across the eight blocks.

Total measured children:

`64`.

## 4. Hard semantic gate

Within every block, all eight conditions must:

- reconstruct the exact integer result;
- emit the same output digest.

Any mismatch blocks the physical frontier.

## 5. Integrated repair gate

For every q:

- old peak - repaired peak must be positive in the block-level confirmatory test;
- all four q tests use Holm familywise alpha 0.05.

Additionally:

- the smallest median peak saving across q must be at least 12 MiB.

If these pass:

`INTEGRATED_CENTER_REPAIR_QUALIFIED`.

## 6. New q surface

For repaired q={1,2,4,7}, B487 freezes:

- median normalized peak;
- median work time;
- peak delta vs repaired q1;
- latency ratio vs repaired q1;
- exact two-objective Pareto q set.

No B469 numerical threshold is copied into the new surface.

## 7. Why paired old/new matters

The repaired and old implementations are measured in the same runner-block
generation and use the same workload content.

This separates implementation repair from:

- hosted-runner epoch drift;
- workload-seed differences;
- historical calibration changes.

## 8. Claim ceiling

**HOSTED_PAIRED_OLD_VS_REPAIRED_Q_FRONTIER**

## 9. Next

If B487 qualifies:

1. retire B475 thresholds for the repaired runtime;
2. use the repaired q surface as the new physical prior;
3. rebuild sample-max calibration and coverage-aware Governor on the repaired
   implementation.

The old Governor remains valid only for the old centering implementation.
