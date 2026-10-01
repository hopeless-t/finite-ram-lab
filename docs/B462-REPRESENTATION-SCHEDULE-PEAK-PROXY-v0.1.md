# B462 — Representation Schedule Physical Peak Proxy v0.1

Status: **BOUNDED HOSTED PHYSICAL PROXY**.

## 1. Question

B461 proved an exact software statement:

- the streamed CRT fold preserves the exact result;
- the frozen logical model needs less simultaneous intermediate representation.

B462 asks only the next physical question:

> Does a matched all-resident versus streamed materialization schedule produce the
> expected direction in process peak residency on a hosted Linux runner?

This is deliberately narrower than benchmarking an Ozaki kernel.

## 2. Why this experiment is a proxy

The experiment materializes page-backed anonymous buffers sized from the B461
representation model.

It does **not** claim that these buffers are the implementation strategy of any
particular Ozaki library.

The value of the experiment is methodological:

- exact semantic gate first;
- physical schedule second;
- fresh process per arm;
- normalized peak instead of final RSS;
- order-balanced matched pairs.

## 3. Frozen geometry

Seven residue lanes:

`[127,125,121,119,113,109,107]`.

Element count:

`4,194,304 = 2048^2`.

Each residue lane is one logical byte per element.

The final CRT fold-state width under the frozen representation model is seven
bytes per element.

Therefore expected simultaneously live materialization is:

### ALL_RESIDENT

```text
7-byte accumulator + seven 1-byte lanes
= 14 bytes/element
= 58,720,256 bytes
= 56 MiB
```

### STREAMED_FOLD

```text
7-byte accumulator + one 1-byte lane
= 8 bytes/element
= 33,554,432 bytes
= 32 MiB
```

Modeled live-state difference:

`24 MiB`.

These are expected materialized buffer bytes, not expected exact VmHWM deltas.

## 4. Physical measurement

Every arm runs in a fresh Python process.

Before materialization the child:

1. executes the B461 exact CRT semantic gate;
2. collects garbage;
3. freezes baseline `VmHWM` and `VmRSS`.

Buffers are anonymous `mmap` objects and every page is touched.

Primary metric:

```text
normalized_peak_growth
=
observed VmHWM - baseline VmHWM
```

The streamed arm closes each residue lane before constructing the next one.

The all-resident arm retains all residue lanes through the observation point.

## 5. Pairing

Six matched pairs are frozen.

Order alternates:

```text
pair0: reference -> treatment
pair1: treatment -> reference
pair2: reference -> treatment
pair3: treatment -> reference
pair4: reference -> treatment
pair5: treatment -> reference
```

Because every arm is a fresh process, the order is mainly a guard against
host-time drift rather than allocator carry-over.

Strict physical gate:

```text
treatment normalized peak - reference normalized peak < 0
```

for all six pairs.

If one pair violates the gate, preserve the result and run a targeted biopsy;
do not rewrite it as noise.

## 6. Relationship to PCG A1

This is a direct method transfer from the PCG dead-strip lane:

- semantic correctness and physical benefit are separate;
- normalized peak growth is primary;
- final RSS is supporting only;
- reference/treatment order is balanced;
- rare contrary pairs trigger targeted biopsy.

The mechanisms differ. The experimental discipline is shared.

## 7. Claim ceiling

**HOSTED_LINUX_MMAP_REPRESENTATION_SCHEDULE_PROXY**

A PASS establishes only that the representation-schedule distinction produces a
reproducible peak-residency direction in the declared hosted environment.

It does not establish:

- Ozaki kernel speedup;
- production allocator behavior;
- GPU/VRAM behavior;
- general Linux universality;
- ternary or Kitten runtime performance.

## 8. If PASS

The next stronger bite should replace proxy buffers with a real numerical
implementation while retaining the same matched-process measurement contract.

That experiment should ask whether streamed residue production/reconstruction
can retain exact output and lower the measured peak without unacceptable
latency/traffic cost.
