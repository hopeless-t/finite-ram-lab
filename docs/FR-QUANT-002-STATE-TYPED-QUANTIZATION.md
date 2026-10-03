# FR-QUANT-002 — State-typed Quantization

Status: **SOURCE-GROUNDED FORMULAS + SYNTHETIC SELECTION**

Parent: **FR-SHARE-001**

## Why this lane exists

Finite RAM Lab already included AWQ, GPTQ, NF4, GGUF, BitNet, FP8 and NVFP4
relatives.

That is not the same as exhausting quantization.

The previous graph was primarily model-weight oriented.

This lane makes the quantized **state class** explicit:

- weights;
- activations;
- KV cache;
- outliers;
- quantization metadata / codebooks;
- native low-bit architecture.

## First correction: "4 bit" is not necessarily 4 effective bits

For grouped quantization:

[
b_{eff}
=
b_{payload}
+
rac{
b_{scale}+b_{zero}
}{
g
}.
]

For a nominal 4-bit payload with a 16-bit scale and 16-bit zero point:

| group size | effective bits/weight |
|---:|---:|
| 32 | **5.0** |
| 128 | **4.25** |

If the metadata itself is reduced to 8+8 bits:

| group size | effective bits/weight |
|---:|---:|
| 32 | **4.5** |
| 128 | **4.125** |

Therefore:

[
oxed{
	ext{label bit-width}

eq
	ext{physical effective bit-width}
}
]

Quantization scales, zero points, codebooks, alignment and outlier metadata must
be counted.

QLoRA is a useful relative because NF4 is paired with **double quantization**,
which also compresses quantization constants rather than treating metadata as
free.

## Weight quantization families

### AWQ / GPTQ

Already represented as conventional low-bit weight PTQ families.

### AQLM

Pinned as an additive/codebook relative for the extreme 2–3 bit regime.

### QuIP#

Pinned as an extreme low-bit relative using incoherence processing and lattice
codebooks.

### SpQR

Pinned as a distinct representation family:

- low-bit bulk weights;
- selected difficult outliers retained at higher precision;
- sparse location/index overhead.

A simple accounting model is:

[
b_{eff}
=
(1-f)b_{bulk}
+
f(b_{high}+b_{index}).
]

For the frozen synthetic example:

- bulk = 3 bits;
- outliers = 0.5%;
- high precision = 16 bits;
- index = 16 bits;

the effective density is:

[
3.145 bits/weight.
]

This is not a measured SpQR checkpoint size.

It demonstrates why **outlier escape is its own atom**.

## Activation quantization

SmoothQuant is now pinned as the first explicit activation-quantization
relative.

Its central relevance to Finite RAM is that it enables an W8A8 path by
redistributing activation outlier difficulty into weights.

This targets a different memory surface from weight-only quantization.

For one synthetic activation buffer:

[
1	imes4096	imes4096
]

elements:

- FP16 = 32 MiB;
- 8-bit activation representation = 16 MiB.

Real inference peak memory depends on buffer lifetimes and kernels; this is only
geometry.

## KV quantization

KIVI is pinned as an explicit KV-cache quantization relative.

Long-context KV can remain huge after the model weights are aggressively
quantized.

Frozen example:

- 32 layers;
- 32,768 tokens;
- 8 KV heads;
- head dimension 128;
- batch 1.

Raw geometry:

[
M_{KV}
=
2LTHDrac{b}{8}.
]

At FP16:

**4096 MiB**.

At an illustrative effective 2.5 bits:

**640 MiB**.

That is an 84.375% byte reduction for this geometry.

The 2.5-bit value is a synthetic effective accounting point, not a claim about
KIVI's exact metadata footprint on every model.

## Why KV belongs beside, not under, weight quantization

A system can have:

- 4-bit weights;
- 16-bit KV;
- 16-bit activations.

Or:

- 4-bit weights;
- 2-bit KV;
- 8-bit activations.

Those are different physical memory systems.

Therefore:

[
oxed{
Q
=
(Q_W,Q_A,Q_{KV},Q_{meta},Q_{outlier})
}
]

rather than one global "model bit-width".

## Dynamic mixed precision

The natural next controller is state-dependent.

Examples:

- hot/sensitive layer -> 8/16-bit;
- ordinary layer -> 4-bit;
- cold/reconstructible shard -> 2–3-bit codebook;
- KV keys/values -> separate quantization rules;
- rare outlier channels -> high-precision escape.

The controller should optimize **effective bytes + restore/dequant cost +
quality risk**, not the marketing label "Q4".

## Synthetic selection fixture

This lane includes synthetic quality proxies only to test the planner topology.

At a weight quality floor 0.98, the frozen toy table selects the SpQR-like
outlier representation because it has the smallest eligible effective density.

At 0.97 it selects the QuIP#-like extreme representation.

For hot activations with floor 0.99 it selects the SmoothQuant-like W8A8
candidate.

For KV with floor 0.98 it selects the KIVI-like candidate.

These selections are **not benchmark rankings of the real methods**.

They prove only that different semantic state classes can rationally select
different quantization families.

## What is still not "done"

Even after this lane, quantization research remains open.

Important future axes:

- per-layer sensitivity measured on real models;
- per-token / runtime precision switching;
- real kernel support and dequant workspace;
- GGUF K/IQ tensor types and alignment overhead;
- calibration cost;
- CPU vs GPU decode kernels;
- quantization × sharing factorial interaction;
- quantization × SSD/cloud transfer;
- quantization × page-cache behavior;
- quality/tail failures rather than a scalar proxy.

## Strong new invariant

[
oxed{
	ext{quantization is a vector of state-specific representations,
not one model-wide number}
}
]

## Claim ceiling

**SOURCE_GROUNDED_FORMULA_AND_SYNTHETIC_STATE_TYPED_QUANTIZATION_ONLY**
