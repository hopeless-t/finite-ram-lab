# B484 — Isolated Centering Temporary v0.1

Status: **PRIMITIVE-LEVEL MECHANISM TEST**.

## 1. Hypothesis from B483

B483 localized the content-sensitive HWM difference to one final statement:

```python
mask = accumulator > half
accumulator[mask] -= modulus_product
```

The HWM difference appeared only after centering, while current RSS did not show a
stable content difference.

A candidate explanation is NumPy boolean advanced indexing.

The expression `accumulator[mask]` creates a selected-value temporary whose
size scales with the number of True elements.

## 2. Why the content counts are predictive

The CRT result before centering represents negative exact products as large
positive residues above half the modulus product.

Therefore:

```text
mask True count
=
number of negative exact products
```

for this workload.

For the frozen seed-derived contents:

- content474 negative products = 2,068,892
- content476 negative products = 2,051,952
- difference = -16,940 elements

If the selected int64 temporary dominates the content-dependent part:

```text
predicted byte delta
=
-16,940 * 8
=
-135,520 B
```

B482 observed approximately this magnitude.

## 3. Primitive isolation

B484 removes:

- input loading;
- residue generation;
- CRT folding;
- q-dependent residency.

The measured child starts with one equal-size int64 accumulator.

Before the measurement baseline, exactly N elements are assigned a value above
the CRT half threshold.

Then the child runs only the existing `_center_in_place` primitive.

## 4. Controlled selected counts

Four count levels are frozen:

- 1,000,000
- 2,051,952 (content476 geometry)
- 2,068,892 (content474 geometry)
- 3,000,000

Every array has the same total element count:

`2048^2 = 4,194,304`.

The boolean mask is therefore always the same size.

Only the selected int64 payload count changes.

## 5. Runner-block design

Eight independent GitHub-hosted jobs.

Every count level runs twice in fresh child processes.

Within a block, the second order reverses the first.

Total measured children:

`8 blocks * 4 levels * 2 = 64`.

## 6. Confirmatory predictions

Two independent shape predictions are frozen.

### Actual content pair

```text
HWM(content476) - HWM(content474) < 0
```

and the observed magnitude should be reasonably close to:

`-135,520 B`.

### Wide count span

```text
HWM(3,000,000) - HWM(1,000,000) > 0
```

The implied HWM slope should be near:

`8 bytes / selected element`.

B484 uses a bounded mechanism gate:

- both directional block tests significant after Holm correction;
- median slope between 6 and 10 B/selected element;
- median actual-pair prediction error <=25%.

## 7. RSS diagnostic

Current RSS immediately after the primitive returns is recorded separately.

A transient selected-value copy can raise HWM and then disappear before the RSS
snapshot.

Therefore a weak or inconsistent post-operation RSS difference is compatible
with the proposed mechanism.

## 8. Claim ceiling

**ISOLATED_NUMPY_BOOLEAN_INDEX_CENTERING**

A PASS establishes the mechanism for this NumPy implementation and primitive. It
does not imply that arbitrary numerical workloads are inherently
content-sensitive in memory.

## 9. Consequence

If B484 passes, the earlier apparent workload-content resource effect should be
reclassified:

```text
general workload-content peak effect
    ->
implementation-specific centering temporary
```

The production Governor should not learn seed/content as a resource feature from
B482.

The engineering next step is a center implementation that avoids
selected-value materialization, followed by exactness and HWM comparison.
