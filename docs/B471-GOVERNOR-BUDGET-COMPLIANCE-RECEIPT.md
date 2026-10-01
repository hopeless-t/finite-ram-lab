# B471 — Governor Budget Compliance Receipt

Status: **PASS / CALIBRATION REQUIRED**

## Frozen execution

- workflow run: 36933903103
- job: 110609522931
- execution head: c5e59c089e670503b7de9fcb542aabf6651381f7
- targeted tests: 4/4 PASS
- artifact ID: 11196898737
- artifact ZIP SHA256: 72379809277115cc3299a76871cd87e89edf9af5c8d092f32f1b4ced6c435179
- panel SHA256: b1b1b11b0ba50753a2673db2c776d4732c7a53dd1a8bc35cb8e40604600b8022

## Overall

Fresh-process observations:

`16`

Budget compliant:

`14/16`

Budget misses:

`2/16`

Classification:

**BOUNDARY_BUDGET_CALIBRATION_REQUIRED**

All 16 observations preserved exact semantics.

## q=1 boundary

Declared observed-upper budget:

`67,022,848 B`

Observed peaks:

```text
67,022,848
67,108,864
67,022,848
67,117,056
```

Compliance:

`2/4`

Largest observed peak:

`67,117,056 B`

Maximum budget overrun:

`94,208 B = 23 * 4096 B pages`

The old four-sample observed upper was therefore not a future upper bound.

## q=2 boundary

Budget:

`67,108,864 B`

Compliance:

`4/4`

Largest new observed peak:

`67,043,328 B`

Minimum margin:

`65,536 B`

## q=4 boundary

Budget:

`71,303,168 B`

Compliance:

`4/4`

Largest new observed peak:

`71,217,152 B`

Minimum margin:

`86,016 B`

## q=7 boundary

Budget:

`71,507,968 B`

Compliance:

`4/4`

Every new observation landed exactly at:

`71,507,968 B`

This repeatability is notable but is not promoted to a universal guarantee.

## Interpretation

The governor decision structure survived dogfood.

The only calibration failure was the q=1 empirical boundary.

This sharpens the model:

```text
observed_upper
!=
guaranteed_upper
```

and shows that uncertainty is q-dependent.

q=1 exhibited a wider fresh-run peak tail than the original B469 sample revealed.

## Next

B472 should target q=1 only.

Use the union-observed boundary:

`67,117,056 B`

as the new empirical reference and run a larger independent fresh-process panel.

Do not call that value a safety guarantee.

The purpose is to estimate whether the q1 upper frontier is still moving and to
measure the additional headroom required by new specimens.
