# FR-P9-021 — Physical CPU + transfer ServiceCurve conjunction

## Purpose

FR-P9-020 analytically proved that multi-resource residency admission must be a typed conjunction rather than an illegal scalar sum across incompatible units. FR-P9-021 builds the smallest hosted physical proxy with two independently controllable resource-service channels.

This is not a disk benchmark or CPU scheduler benchmark. The transfer lane is deliberately **userspace paced**: bytes are read from a temporary file and become available to the runtime only after an explicit per-chunk service gate. The CPU lane is a fixed number of SHA-256 work quanta, optionally delayed by a controlled CPU-service start gate.

## Resource obligations

```text
TRANSFER: 4 MiB delivered-to-runtime bytes by 100 ms
CPU:      4 completed SHA-256 quanta by 100 ms
```

All lanes process the same source bytes and compute the same semantic signature.

## Frozen lanes

- `FAST_FAST`: no transfer pacing delay, no CPU service gate.
- `SLOW_TRANSFER`: 35 ms service delay per 1 MiB chunk, CPU otherwise fast.
- `SLOW_CPU`: transfer fast, CPU service delayed 140 ms.
- `SLOW_BOTH`: both delays active.

Lane order reverses on the middle repetition.

## Qualification rule

```text
typed_feasible =
    transfer_bytes_at_deadline >= 4 MiB
    AND
    cpu_quanta_at_deadline >= 4
```

The typed prediction is compared with the actual end-to-end completion timestamp on every run.

The important falsifiers are asymmetric:
- full CPU service must not compensate for transfer deficit;
- full transfer service must not compensate for CPU deficit.

## Boundary

The pacing gates dominate the service timing intentionally. Therefore results support only the resource-conjunction contract, not claims about real SSD bandwidth, filesystem cache behavior, Linux CPU scheduling, SHA throughput, or application performance.

`resource-feasible != authority`; no lane grants retry permission.

## Next gate

After confirming two independent resources, model **stage dependencies and composition**. A transfer service curve that delivers bytes late changes when CPU reconstruction can even begin; end-to-end admission therefore needs a composition operator, not merely independent per-resource checks.

Claim ceiling:
`HOSTED_GITHUB_USERSPACE_PACED_FILE_TRANSFER_AND_CPU_HASH_PROXY_ONLY_NO_MEDIA_BANDWIDTH_CPU_SCHEDULER_OR_APPLICATION_CLAIM`
