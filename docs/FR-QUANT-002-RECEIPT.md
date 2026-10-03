# FR-QUANT-002 — State-typed Quantization Receipt

Status: **PASS / STATE-TYPED QUANTIZATION ACCOUNTING VALIDATED**

## Qualification

- workflow run: 37111908321
- job: 111171296195
- execution head: 090b29b8c6426f3ed7d9fa99e1a045a5fa143750
- artifact ID: 11270043329
- artifact ZIP SHA256: ceead426d8efe1807cef12917f716ab57989a5a2b7c1c7f013262da69cfd1828
- spec SHA256: 0710e8e4979af2e4a3ea9f42c84b5b4d3949f55f863bb46c76ad345774b20cc9
- result SHA256: 013495644792b3a3ce3518d300e341e9fa352037b0f18af2acf479f033a45d0d

## Frozen accounting examples

Grouped nominal Q4:

- group 32, 16-bit scale + 16-bit zero: 5.0 effective bits/weight
- group 128, same metadata: 4.25 effective bits/weight
- group 32, 8+8-bit metadata: 4.5 effective bits/weight
- group 128, 8+8-bit metadata: 4.125 effective bits/weight

Outlier-escape example:

- 3-bit bulk
- 0.5% FP16 outliers
- 16-bit index/outlier
- effective density: 3.145 bits/weight

## KV geometry

32 layers / 32K tokens / 8 KV heads / head dim 128 / batch 1:

- FP16 KV: 4096 MiB
- illustrative effective 2.5-bit KV: 640 MiB
- byte reduction: 84.375%

## Activation geometry

1 x 4096 x 4096 activation buffer:

- FP16: 32 MiB
- 8-bit: 16 MiB

## Boundary

All quality proxies used for selection are synthetic controls.

This receipt does not rank real AWQ/GPTQ/SpQR/AQLM/QuIP#/SmoothQuant/KIVI
implementations.

## Main invariant

`quantization is a vector of state-specific representations, not one model-wide number`.

## Claim ceiling

**SOURCE_GROUNDED_FORMULA_AND_SYNTHETIC_STATE_TYPED_QUANTIZATION_ONLY**
