# FR-XFER-001 — Transfer/Staging Peak Tax

Status: **HOSTED LINUX PHYSICAL PROXY**

Parent: **FR-NORTHSTAR-004**

## Why this lane exists

This is the first mechanism lane created **after** the North-Star reset.

It was not opened because transfer buffers looked interesting.

FR-NORTHSTAR-004 classified:

`TRANSFER_STAGING_PRESSURE`

as the only frozen **CAPABILITY_GAP** in its five-case panel.

That gives FR-XFER-001 a direct North-Star justification.

## Question

Can an operation that ultimately reduces resident memory still fail because the
migration itself creates a larger temporary peak?

Yes, if source, staging, and destination coexist.

The atomic accounting is:

[
M_{peak}^{move}
=
M_{source}
+
M_{staging}
+
M_{destination}
+
M_{metadata}.
]

The final state may be smaller than the initial state while the transfer peak is
larger than both.

## Physical proxy

Each arm runs in a fresh Python process on Linux.

Payload:

**32 MiB**

Primary metric:

baseline-subtracted process **PSS** from `/proc/self/smaps_rollup`.

Arms:

### SOURCE_ONLY

Hold one fully materialized 32 MiB bytearray.

Expected geometry:

[
approx 1	imes payload.
]

### DIRECT_COPY

Hold:

- source;
- destination copy.

Expected geometry:

[
approx 2	imes payload.
]

### STAGED_COPY

Hold simultaneously:

- source;
- immutable staging copy;
- destination copy.

Expected geometry:

[
approx 3	imes payload.
]

### SHARED_VIEW

Hold:

- source;
- read-only memoryview.

No payload copy is intended.

Expected geometry:

[
approx 1	imes payload.
]

## Why this matters to Finite RAM

Many earlier actions can hide a transfer peak:

- SSD -> RAM restore;
- RAM -> VRAM promotion;
- cloud -> RAM fetch;
- dequantization workspace;
- compressed -> decompressed state;
- model shard migration;
- double buffering;
- page-cache -> application copy.

A controller that checks only the **final** memory state can authorize an action
that crosses the OOM/pressure knee during the move.

Therefore:

[
oxed{
	ext{final relief}

eq
	ext{safe migration}
}
]

and:

[
oxed{
max_t M(t)
	ext{ must be qualified, not only } M_{after}
}
]

## Qualification gates

The hosted proxy requires median baseline-subtracted PSS ratios:

- SOURCE_ONLY: 0.70–1.35x payload;
- DIRECT_COPY / SOURCE_ONLY: 1.60–2.40x;
- STAGED_COPY / SOURCE_ONLY: 2.50–3.50x;
- SHARED_VIEW / SOURCE_ONLY: 0.80–1.20x.

These are deliberately broad physical-geometry gates.

They are not portable performance thresholds.

## Boundary

This is **not** a CUDA or GPU transfer benchmark.

It does not claim:

- pinned-memory behavior;
- PCIe bandwidth;
- DMA overlap;
- GPU zero-copy viability;
- RAM->VRAM ratios;
- development-machine safety margins.

It isolates the host-memory staging atom first.

## North-Star integration

If qualified, FR-XFER-001 should add a new primitive:

`TRANSFER_WITH_PEAK_BUDGET`

or, when semantics allow:

`ZERO_COPY_SHARED_VIEW`.

Every tier-migration primitive should then expose:

- source resident bytes;
- staging bytes;
- destination bytes;
- transient peak;
- release ordering;
- transfer deadline.

The shadow compiler can reject a migration when:

[
M_{current}
+
M_{transfer peak}
>
M_{budget}
]

even if the final state would fit.

## Next

After qualification:

1. register the transfer-peak effect model;
2. rerun FR-NORTHSTAR-004;
3. verify the CAPABILITY_GAP closes;
4. **stop transfer research unless the frontier still misses**.

That last step is the new research discipline.

## Claim ceiling

**HOSTED_LINUX_PYTHON_TRANSFER_STAGING_PROXY_ONLY**
