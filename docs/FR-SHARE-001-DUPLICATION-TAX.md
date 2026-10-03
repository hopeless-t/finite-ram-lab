# FR-SHARE-001 — Duplication Tax

Status: **HOSTED LINUX PHYSICAL PSS EXPERIMENT**

Parent: **FR-ATOM-001**

## Question

If several workers need the same immutable state, should Finite RAM Lab spend
its next unit of complexity on another bit of quantization, or on eliminating
duplicate physical copies?

This experiment isolates the duplication multiplier (D).

## Fixture

Six Python worker processes consume the same 32 MiB immutable payload.

Three fresh-process arms:

1. **BASELINE** — worker runtime only;
2. **PRIVATE_COPY** — each worker reads the entire payload into its own
   `bytearray`;
3. **SHARED_MMAP** — each worker maps the same file read-only and touches every
   page.

The payload contents and worker count are identical.

## Why PSS rather than summed RSS

RSS charges a shared page to every process mapping it.

Therefore summing RSS can make one shared physical page look like six pages.

Linux `smaps_rollup` exposes proportional set size (PSS), which apportions a
shared page across the processes using it.

The primary physical-process metric is:

[
Delta PSS_{arm}
=
sum_i PSS_i^{arm}
-
sum_i PSS_i^{baseline}.
]

## Expected geometry

Nominal private payload:

[
6	imes32 MiB=192 MiB.
]

Nominal shared payload:

[
32 MiB.
]

The expected ideal ratio is therefore roughly:

[
1/6approx0.167.
]

Allocator/runtime/kernel effects mean the experiment does not require the exact
ideal ratio.

The frozen qualification gate is deliberately loose:

[
rac{Delta PSS_{shared}}
{Delta PSS_{private}}
<0.35.
]

## Why this matters to quantization

Suppose a representation uses 4-bit weights, a 4x byte reduction, but eight
workers independently materialize it:

[
8	imes0.25=2.0
]

full-precision-equivalent copies.

One shared FP16 immutable copy is:

[
1	imes1.0=1.0.
]

This does not mean FP16 sharing is generally better.

It means:

[
oxed{
Q 	ext{ (representation density) and }
D 	ext{ (duplication) must be optimized together.}
}
]

## Boundary

This experiment does not enable KSM and writes no sysfs values.

It tests ordinary file-backed sharing only.

Writable KV cache, optimizer state, mutable activations, and private scratch
buffers have different sharing semantics.

Global page-cache memory is also not fully attributed by the child-process PSS
comparison, so the experiment does not claim total-system memory from PSS alone.

## Next

If the physical sharing effect qualifies:

1. **FR-SHARE-002** — quantization × sharing factorial experiment;
2. **FR-SHARE-003** — copy-on-write mutation rate / break-even;
3. **FR-SHARE-004** — shared model arena across tiny worker processes;
4. optional KSM experiment only when kernel/config permissions are explicitly
   available and CPU scan cost is measured.

## Claim ceiling

**HOSTED_LINUX_IMMUTABLE_PROCESS_PSS_SHARING_ONLY**
