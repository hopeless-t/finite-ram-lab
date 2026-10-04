# FR-FP-048 Receipt

Status: **PASS / HOSTED PHYSICAL VARIABLE-SIZE DIRECTIONAL MIGRATION COST QUALIFIED**

Parent: **FR-FP-047**

Final qualification:
- workflow run: 37219146828
- job: 111485741694
- execution head: 4b86c71a3c4507f2c4c8f2bce2de25150aad921c
- physical actions: 42
- sizes: 4 / 6 / 8 / 10 / 12 / 14 / 16 MiB
- repeats per size and direction: 3

All promotion cycles:
- start <=10% resident
- end >=95% resident
- prefetch exactly the state byte size

All eviction cycles:
- start >=95% resident
- end <=10% resident

## PROMOTE model

Affine fit:

    promote_ms
      ~= 2.282833
       + 1.730256 * state_MiB

- R^2: 0.94046
- constant-per-action LOO MAE: 7.2071 ms
- affine-byte LOO MAE: 1.9571 ms
- held-out error improvement: 72.84%

Preferred:

    AFFINE_BYTES

## EVICT model

Affine fit:

    evict_ms
      ~= 10.115819
       + 0.032783 * state_MiB

- R^2: 0.95861
- constant-per-action LOO MAE: 0.13130 ms
- affine-byte LOO MAE: 0.02376 ms
- held-out error improvement: 81.90%

Preferred:

    AFFINE_BYTES

Interpretation:

Promotion cost has a strong byte term.

Eviction also has a measurable byte term, but the qualified actuator's
intentional settle overhead dominates its absolute latency.

These coefficients describe the existing hosted actuator contract, including
settle sleeps. They are not raw kernel-I/O coefficients.

Decision:

**SELECT_DIRECTIONAL_MIGRATION_COST_MODEL_BY_HELD_OUT_SIZE_ERROR_NOT_BY_EQUAL_SIZE_ASSUMPTION**

Next:

Use the frozen directional byte-cost model inside a joint migration-aware exact
byte-budget placement optimizer.

Claim ceiling:

**HOSTED_PHYSICAL_DIRECTIONAL_MIGRATION_COST_ON_SEVEN_STATE_SIZES_AND_THREE_REPEATS_ONLY**
