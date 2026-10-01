# B483 — Stage HWM/RSS Biopsy Receipt

Status: **PASS / FIRST DIVERGENCE LOCALIZED TO CENTERING**

## Frozen execution

- workflow run: 36939641405
- aggregate job: 110628073856
- execution head: 382e4b30bf059c7529a0e2d2ca9d58eff66b881d
- targeted tests: 3/3 PASS
- runner blocks: 8
- aggregate artifact ID: 11199421940
- artifact ZIP SHA256: 53f68a62e35802e337737aec1fc46ef86b2f7ec2a28f6670ead855f17b53c5e8
- aggregate JSON SHA256: 9487db80b292a85cf1c6cad318aa98d20747ea144e580f339c78902ca7aec94c

The initial B483 workflow run 36939555595 is invalid for scientific use because
a variable-name bug stopped the instrumented child before a valid panel. The
corrected full runner-block panel is the execution above.

## Confirmatory final effect

q2:
- final HWM lower for content476 in 8/8 runner blocks
- p=0.00390625
- Holm significant

q4:
- final HWM lower for content476 in 8/8
- p=0.00390625
- Holm significant

The B482 content-sensitive HWM effect therefore replicated in the stage-biopsy
panel.

## Localization

For both q2 and q4:

```text
pre_load
post_load
post_accumulator
residue production
CRT folds
group releases
...
post_center  <-- first unanimous HWM divergence
```

q2 post-center median HWM delta:

`-132,096 B`

q4 post-center median HWM delta:

`-138,240 B`

No milestone reached an 8/8 current-RSS divergence.

Therefore the signal has the signature of a transient allocation that affects
the historical high-water mark and is no longer consistently resident after the
operation.

## Candidate mechanism

The current centering primitive is:

```python
mask = accumulator > half
accumulator[mask] -= modulus_product
```

Boolean advanced indexing can materialize a temporary containing the selected
int64 elements.

For the deterministic rank-1 content:

seed474 sign counts:
- left: 999 negative, 13 zero, 1036 positive
- right: 998 negative, 14 zero, 1036 positive
- negative outer products: 2,068,892

seed476:
- left: 989 negative, 25 zero, 1034 positive
- right: 1028 negative, 20 zero, 1000 positive
- negative outer products: 2,051,952

Difference:

`-16,940 selected elements`

At 8 bytes per selected int64 value:

`-135,520 B`

This predicted selected-payload difference is strikingly close to the observed
~132-138 KiB HWM difference.

B483 does not promote this correlation to mechanism proof because the milestone
search was descriptive.

## RSS clue

The post-center current-RSS delta is not unanimous, even while HWM is 8/8 lower
for content476.

That is consistent with a short-lived temporary allocation during the centering
statement rather than a persistent resident-state difference.

## Claim ceiling

**DESCRIPTIVE_STAGE_HWM_BIOPSY**

## Next

B484 should isolate centering only.

Use pre-materialized equal-size int64 accumulator arrays with controlled counts
above the CRT half-range threshold.

Hard prediction:

```text
HWM difference
approximately tracks
8 bytes * difference in selected-element count
```

while post-operation current RSS should converge.

If the effect survives this primitive-only test, the apparent workload-content
memory signal is an implementation-level boolean-index temporary, not a general
property of the numerical obligation.
