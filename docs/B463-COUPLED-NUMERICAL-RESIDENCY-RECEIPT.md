# B463 — Coupled Numerical Residency Receipt

Status: **PASS / EXACT + LOWER PEAK REPLICATED**

## Frozen execution

- workflow run: 36927364546
- job: 110587892643
- execution head: 2cd2ea672ede6906900c28c853cc4bb6b4c4f50c
- targeted tests: 3/3 PASS
- artifact ID: 11195070024
- artifact ZIP SHA256: a440e6602157607cdb22417266e05432ce8dd0d951d6548ab7bda1f8c4356ca2
- panel JSON SHA256: c78b60339f7ff9e0ad2d202e0c90864333049430287c099a4d8b245cf02c7e3d

## Exact numerical path

Both arms executed the same deterministic 2048x1 by 1x2048 integer matrix product
through seven residue lanes and CRT reconstruction.

Every matched pair passed the hard semantic gate:

- reference exact = true
- treatment exact = true
- output digest equal
- semantic match = 6/6

## Physical peak result

Treatment minus reference normalized VmHWM growth:

```text
-25,153,536 B
-25,194,496 B
-25,157,632 B
-24,989,696 B
-25,112,576 B
-25,190,400 B
```

Summary:

- negative = 6/6
- positive = 0/6
- zero = 0/6
- median = -25,155,584 B
- median ~= **-23.99 MiB**

Classification:

**COUPLED_EXACT_PEAK_EFFECT_REPLICATED**

The measured effect is extremely close to the frozen logical 24 MiB residency
difference, but the experiment does not require exact byte-for-byte equality.

## Latency result

Treatment/reference work-time ratios:

```text
1.06194
1.06657
1.06071
1.04912
1.05527
1.04387
```

Median ratio:

**1.05799**

Median streamed-fold penalty in this implementation:

**+5.80%**

This is an important result rather than a failure.

B463 demonstrates an explicit exchange:

```text
~24 MiB lower process peak
for
~5.8% median work-time increase
```

under this hosted NumPy rank-1 residue/CRT implementation.

The result therefore belongs on a Pareto frontier rather than being collapsed to
a single "better/worse" score.

## Evidence chain after B463

```text
exact future obligation
  -> future-sufficient incremental CRT state
  -> actual residue production and release
  -> exact final numerical equality
  -> ~24 MiB lower normalized peak
  -> measurable ~5.8% latency cost
```

This is the first implementation-level memory/latency tradeoff specimen in the
obligation-residency lane.

## Claim ceiling

**HOSTED_NUMPY_RANK1_RESIDUE_CRT_IMPLEMENTATION**

Do not generalize the 5.8% latency ratio to:

- dense GEMM;
- GPU kernels;
- production Ozaki implementations;
- other allocators or machines.

## Consequence

The governor must not optimize RAM alone.

It needs a constrained/Pareto decision surface over at least:

- fidelity;
- peak residency;
- latency;
- useful work;
- later, traffic/energy where measured.

That makes B464's OBSERVE / OPTIMIZE / PROBE split a direct continuation rather
than a product detour.
