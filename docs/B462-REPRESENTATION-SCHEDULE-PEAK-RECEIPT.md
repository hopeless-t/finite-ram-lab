# B462 — Representation Schedule Physical Peak Proxy Receipt

Status: **PASS / PHYSICAL PEAK DIRECTION REPLICATED**
Date: 2026-10-02

## Frozen execution

Workflow: B462 Representation Peak Proxy
Run: 36924274517
Job: 110577608824
Execution head: 29672bd7793fb24747ead7ef8379aa9ecb859c02

Targeted tests:
- 3 tests
- 3 PASS
- runtime 0.001 s

Artifact:
- ID: 11192913454
- ZIP SHA256: d44d13d54595aa4b91daed7e07f5f1021094538e7f8c484d423e2f35f6281b14
- panel JSON SHA256: 9f8cbdf2494fedf787c2cbb010ccdde70461c941b644e6ad393bdc9d7cdda0d8

## Frozen matched panel

Geometry:
- hosted ubuntu-24.04
- anonymous page-touched mmap buffers
- fresh process per arm
- 6 matched pairs
- alternating reference-first / treatment-first
- element count = 4,194,304
- lane count = 7
- moduli = [127,125,121,119,113,109,107]
- exact B461 semantic gate in every child

Reference:
- ALL_RESIDENT

Treatment:
- STREAMED_FOLD

Primary endpoint:
- normalized VmHWM growth

## Result

Treatment minus reference normalized peak growth, bytes:

```text
-25,165,824
-25,165,824
-25,165,824
-25,165,824
-25,165,824
-25,165,824
```

Summary:
- negative = 6/6
- positive = 0/6
- zero = 0/6
- median = **-25,165,824 B**
- median = **-24 MiB**

Classification:

**PHYSICAL_PEAK_SCHEDULE_EFFECT_REPLICATED**

The observed paired difference exactly matches the frozen materialization model's
24 MiB live-buffer difference for this proxy geometry.

## Interpretation

B461 established that the exact information obligation can be carried by a
streamed CRT fold state without retaining every residue result.

B462 shows that when the resulting representation schedules are materialized as
page-backed host memory, the simultaneous-residency distinction survives as the
expected peak-residency difference in this hosted Linux environment.

The evidence chain is now:

```text
semantic/information obligation
  -> exact future-sufficient fold invariant
  -> lower logical simultaneous representation
  -> lower measured hosted-process peak
```

## Important boundary

This is a representation-schedule proxy.

The experiment does not execute a production Ozaki implementation and does not
claim a GEMM speedup.

The exact semantic gate uses the B461 numerical implementation; the large physical
buffers model its residency geometry independently.

Therefore the current claim ceiling remains:

**HOSTED_LINUX_MMAP_REPRESENTATION_SCHEDULE_PROXY**

## Methodological result

The PCG A1 measurement method transferred cleanly:

- correctness gate first;
- physical-benefit gate second;
- fresh processes;
- order balancing;
- normalized peak as primary endpoint;
- final RSS not used as the primary verdict.

No contrary pair appeared, so no rare-event biopsy is opened for B462.

## Next research edge

A stronger B463 should couple the exact numerical residue production and streamed
reconstruction to the measured memory path itself.

Required gates:

1. exact output equality;
2. normalized peak reduction;
3. latency / traffic accounting;
4. order-balanced replication;
5. no claim beyond the tested implementation/runtime.
