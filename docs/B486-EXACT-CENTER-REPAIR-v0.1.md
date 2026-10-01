# B486 — Exact Tiled Center Repair v0.1

Status: **ENGINEERING REPAIR AFTER CONFIRMED MECHANISM**.

## 1. Mechanism being repaired

B485 confirmed that the old centering primitive:

```python
mask = accumulator > half
accumulator[mask] -= modulus_product
```

creates a selected-value int64 temporary whose HWM cost scales at approximately
8 bytes per selected element.

## 2. Replacement

B486 implements:

```python
mask = np.empty(tile_elements, dtype=bool)

for tile in accumulator:
    np.greater(tile, half, out=mask)
    np.subtract(tile, modulus_product, out=tile, where=mask)
```

Frozen tile size:

`262,144 elements`

The temporary mask is therefore bounded at roughly 256 KiB and reused.

No selected-value array is materialized.

## 3. Primitive comparison

Strategies:

- BOOLEAN_INDEX — existing implementation
- TILED_WHERE — repaired implementation

Selected-count geometries:

- content476 count = 2,051,952
- content474 count = 2,068,892
- high count = 3,000,000

Every child receives the same total 4,194,304-element int64 accumulator.

## 4. Runner blocks

Eight independent GitHub-hosted jobs.

Every block runs all six strategy/count conditions once in fresh processes.

The six-condition order is cyclically shifted across blocks.

Total children:

`48`.

## 5. Exactness gate

For every child:

- exactly selected_count values must become -1;
- all unselected values must remain +1.

Any mismatch blocks resource interpretation.

## 6. Repair qualification

The frozen gate requires:

1. repaired high-count peak is lower in the confirmatory block test;
2. repaired content474-count peak is lower;
3. median high-count peak savings >=16 MiB;
4. median content474-count savings >=12 MiB;
5. repaired content474/content476 HWM sensitivity <=128 KiB in median magnitude;
6. repaired high-vs-content476 HWM sensitivity <=1 MiB;
7. median repaired/old high-count latency ratio <=2.0.

This is intentionally practical: the repaired primitive must remove the large
content-sensitive temporary without creating an extreme latency regression.

## 7. Expected behavior

Old peak:

```text
fixed boolean mask
+
selected_count * 8-byte temporary
+
runtime noise
```

Repaired peak:

```text
bounded tile mask
+
small fixed implementation overhead
```

Therefore repaired HWM should be largely insensitive to selected count.

## 8. Claim ceiling

**ISOLATED_EXACT_CENTER_REPAIR**

A primitive-level PASS does not yet update the q Governor.

## 9. Next

If qualified, B487 must integrate TILED_WHERE into the full residue/CRT numerical
path and remeasure the q={1,2,4,7} Pareto surface.

Only that integrated result may replace the B469/B475 Governor calibration.
