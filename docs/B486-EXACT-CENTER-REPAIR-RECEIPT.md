# B486 — Exact Tiled Center Repair Receipt

Status: **PASS / REPAIR QUALIFIED**

## Frozen execution

- workflow run: 36941106290
- aggregate job: 110632845950
- execution head: a5882a81ebc18066b4f1f7397fc65063acf15b7d
- tests: 4/4 PASS
- runner blocks: 8
- aggregate artifact ID: 11199378740
- artifact ZIP SHA256: 5ae5eddb436fcbf52d6a5b45c30d515caf3ee099d734abefad8a6cb6ae309937
- aggregate JSON SHA256: 8c61d55ff121a77cb9246350798ad4314ca90d814361b2c270f9aafa1a73f728

## Exact replacement

Old:

```python
mask = accumulator > half
accumulator[mask] -= modulus_product
```

Repaired:

```python
mask = np.empty(tile_elements, dtype=bool)

for tile:
    np.greater(tile, half, out=mask)
    np.subtract(tile, modulus_product, out=tile, where=mask)
```

Frozen tile size:

`262,144 elements`

All children preserved the exact selected/unselected values.

## Peak reduction

At the content474 selected-count geometry:

- old content sensitivity remains visible;
- repaired content474/content476 HWM difference median = **-4,096 B**
- median old-to-new peak saving = **20,428,800 B ~=19.48 MiB**

At 3,000,000 selected elements:

- median peak saving = **27,918,336 B ~=26.63 MiB**
- repaired high-count minus repaired content476 peak median = **0 B**

The repaired HWM is therefore effectively insensitive to selected count at this
resolution.

Peak savings were positive in 8/8 runner blocks for both confirmatory geometries.

## Latency

At the high-count geometry:

`median tiled / old latency ratio = 0.33113`

The repaired primitive is roughly three times faster in this isolated hosted
NumPy test.

This is a primitive-level result, not yet a full-workload speedup claim.

## RSS

Both strategies showed the same small post-operation RSS delta in the sampled
high-count blocks.

The large benefit is in avoiding the transient high-water allocation.

## Scientific correction

The research chain is now:

```text
B482: apparent input-content HWM effect
B483: localized to post_center
B484: isolated selected-count scaling, HOLD on small-pair precision
B485: amplified linear response confirms ~8 B/selected int64 temporary
B486: remove temporary -> peak/content sensitivity collapse + faster primitive
```

This converts an apparent workload-content resource property into an
implementation-level temporary-allocation effect.

## Claim ceiling

**ISOLATED_EXACT_CENTER_REPAIR**

## Next

B487 must integrate the repaired centering into the full numerical residue/CRT
path and remeasure q={1,2,4,7}.

The old B469/B475 q frontier remains scientifically valid for the old
implementation but must not be reused as calibration for the repaired runtime.
