# B463 — Coupled Numerical Residency Test v0.1

Status: **HOSTED NUMERICAL IMPLEMENTATION**.

## 1. Goal

B461 proved exact streamed CRT reconstruction in software.

B462 proved that the corresponding residency schedule changes physical peak in a
page-backed proxy.

B463 removes the proxy split.

Residue production, residency, incremental CRT folding, and exact-result checking
now occur in one measured numerical implementation.

## 2. Frozen workload

The workload is a rank-1 integer GEMM:

```text
A: 2048 x 1
B: 1 x 2048
C: 2048 x 2048
```

This geometry is deliberate.

It creates a large output/residue surface while keeping arithmetic cheap enough
for repeated fresh-process GitHub Actions measurements.

It is a real integer matrix product, but it is not a claim about dense production
GEMM performance.

Inputs are deterministic signed int64 values in [-50,50].

Seven pairwise-coprime residue moduli are used:

`[127,125,121,119,113,109,107]`.

Each residue result is stored as uint8.

The CRT fold state is int64 and is updated in 64-row tiles.

## 3. Reference and treatment

### ALL_RESIDENT

1. compute all seven residue GEMM outputs;
2. retain every uint8 residue matrix;
3. allocate/retain the int64 CRT accumulator;
4. fold each retained lane;
5. center the result;
6. verify exact output.

### STREAMED_FOLD

1. keep the int64 CRT accumulator;
2. compute one residue GEMM output;
3. immediately fold it into the accumulator;
4. release the residue lane;
5. repeat;
6. center and verify exact output.

The mathematical obligation is identical.

The physical residency schedule is not.

## 4. Exactness gate

Before a matched pair contributes physical evidence:

- both arms must report exact equality against the direct rank-1 integer product;
- both arms must emit the same output SHA256;
- pairwise-coprime and CRT uniqueness gates must pass.

Any semantic mismatch aborts interpretation.

## 5. Measurement contract

Six matched pairs.

Every arm runs in a fresh process.

Execution order alternates reference-first and treatment-first.

Primary endpoint:

```text
normalized peak growth
=
work-phase VmHWM - pre-work VmHWM
```

Latency is secondary and is measured over residue production + reconstruction,
excluding the later exact-validation sweep.

The experiment records logical live bytes, but physical interpretation comes from
VmHWM.

## 6. Expected residency geometry

For N=2048:

- elements = 4,194,304
- one uint8 residue lane = 4 MiB
- seven lanes = 28 MiB
- int64 accumulator = 32 MiB

Frozen logical live-state accounting:

- ALL_RESIDENT = 56 MiB
- STREAMED_FOLD = 36 MiB
- difference = 20 MiB

The value differs from B462 because B463 uses an 8-byte int64 accumulator rather
than the earlier abstract 7-byte packed fold-state model.

The experiment does not require VmHWM to match these numbers exactly.

## 7. Research value

A PASS would connect:

```text
exact future obligation
-> exact compressed/folded state
-> real numerical residue production
-> altered object lifetime
-> lower measured process peak
```

That would be the first implementation-level evidence in this lane rather than a
pure logical model or materialization proxy.

## 8. Claim ceiling

**HOSTED_NUMPY_RANK1_RESIDUE_CRT_IMPLEMENTATION**

This is not:

- a dense Ozaki GEMM benchmark;
- a GPU result;
- a production-kernel throughput claim;
- evidence that streamed reconstruction is always faster.

The primary scientific question is whether exactness and lower simultaneous
residency coexist in one numerical implementation.

## 9. Next edge

If B463 passes, the next design step should stop being only an Ozaki experiment.

B464 should introduce the common runtime control surface:

```text
OBSERVE | OPTIMIZE | PROBE
```

with intervention receipts that separate:

- production-like optimization runs;
- deliberately perturbed experimental runs;
- passive observation runs.

That is the bridge from Finite RAM experiments to a dogfooded GitHub Actions
research application.
