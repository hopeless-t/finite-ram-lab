# B484 — Isolated Centering Temporary Receipt

Status: **PASS WITH HOLD / MECHANISM GATE NOT YET CLOSED**

## Frozen execution

- workflow run: 36940274240
- aggregate job: 110630073977
- execution head: d1bf06d26100fea6ef727f67cafdbbc2b3f06319
- tests: 4/4 PASS
- runner blocks: 8
- aggregate artifact ID: 11199422802
- artifact ZIP SHA256: 8ba620466cfc99899ee8176a9368a2ae6dfbba8313a775fbbde836010062fdfd
- aggregate JSON SHA256: 3df194625a368df9bb69f9ca8cf91f31fe62ebac470110b609559ebd38f8c4de

## Actual content-pair geometry

Frozen prediction from B483:

```text
selected-count delta = -16,940 elements
payload prediction   = -135,520 B
```

Observed block-level HWM differences were negative in:

`8/8`

Directional sign-test:

`p=0.00390625`

Median observed actual-pair HWM delta:

`-129,024 B`

The median pair effect is close to the prediction.

Post-operation current RSS pair delta median:

`0 B`

## Wide selected-count span

Controlled span:

```text
1,000,000 -> 3,000,000 selected elements
```

HWM increased in:

`8/8 runner blocks`

Directional p:

`0.00390625`

Median observed slope:

`7.998464 B / selected element`

The primitive therefore exhibits an almost exact 8-byte-per-selected-element
HWM slope over the wide controlled span.

## Why the mechanism gate remains HOLD

The frozen B484 mechanism gate also required:

```text
median per-block absolute error
/
135,520 B
<= 25%
```

Observed:

- median absolute per-block prediction error = 44,032 B
- relative error = 32.49%

Individual block actual-pair deltas ranged from approximately -34 KiB to -219 KiB.

Therefore the preregistered gate does not pass, despite:

- 8/8 correct direction;
- median actual effect near prediction;
- wide-span slope essentially exactly 8 B/element;
- zero median post-operation RSS difference.

The result is not rewritten after observation.

Classification remains:

**CENTERING_MECHANISM_NOT_YET_RESOLVED**

## Interpretation

The evidence strongly supports the boolean-index temporary hypothesis, but the
small 135 KiB pair difference is noisy at runner-block HWM resolution.

The next experiment should increase signal amplitude rather than relax the gate.

## Next

B485 should use the same isolated primitive and a symmetric selected-count
difference series around the actual workload region:

- 1x the 16,940-element difference;
- 2x;
- 4x;
- 8x.

If HWM response scales linearly with amplification and converges to ~8 B per
selected element, the small-pair noise can be identified as measurement
resolution/runner variation rather than a failure of the mechanism.
