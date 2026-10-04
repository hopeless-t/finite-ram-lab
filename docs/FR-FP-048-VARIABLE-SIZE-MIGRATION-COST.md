# FR-FP-048 — Variable-size migration cost calibration

Status: **HOSTED PHYSICAL MIGRATION-CALIBRATION CANDIDATE**

Parent: **FR-FP-047**

## Why

FR-FP-042 qualified a direction-specific migration model for equal 8 MiB
states.

FR-FP-047 removed the equal-size assumption and exposed transition costs that
visibly depend on transferred bytes.

FR-FP-048 measures that dependency directly.

## Physical matrix

State sizes:

    4 / 6 / 8 / 10 / 12 / 14 / 16 MiB

For every size, repeat three cycles:

    COLD -> WARM -> COLD

That yields:

    7 sizes x 3 repeats x 2 directions = 42 physical actions

Every promotion must:
- begin <=10% resident;
- end >=95% resident;
- prefetch exactly the file's byte size.

Every eviction must:
- begin >=95% resident;
- end <=10% resident.

## Candidate cost models

Evaluate separately for PROMOTE and EVICT.

### CONSTANT_PER_ACTION

The equal-size-style model:

    cost ~= one direction-specific constant

### AFFINE_BYTES

    cost ~= intercept + slope * state MiB

## Model selection

Do not require one model to win.

For each direction, use leave-one-size-out prediction error.

The lower held-out MAE is the preferred model for the next lane.

This prevents the experiment from manufacturing evidence for the expected
byte-scaling hypothesis.

## Timing boundary

Measured wall time intentionally includes the actuator's existing settle sleeps.

Therefore the fitted model describes:

    this qualified actuator contract

not raw kernel prefetch/fadvise latency in isolation.

## Claim ceiling

**HOSTED_PHYSICAL_DIRECTIONAL_MIGRATION_COST_ON_SEVEN_STATE_SIZES_AND_THREE_REPEATS_ONLY**
