# FR-P9-013 — Compressed reconstruction external-validity probe

## Purpose

FR-P9-011 physically qualified a repeated phase-lifetime tradeoff using a raw private capability plus SHA256-oriented work. FR-P9-012 compiled those measurements into external-price policy regions. FR-P9-013 attempts to falsify the implied horizon ordering with a materially different reconstruction and semantic-work shape.

This is an **external-validity proxy**, not an application benchmark.

## Different physical shape

Cold representation:

- deterministic 16 MiB logical capability;
- stored as gzip-compressed patterned bytes;
- preregistered requirement: compressed source < 1/16 of runtime capability size.

Runtime representation:

- gzip stream reconstructed into a private anonymous writable `mmap`;
- digest checked after reconstruction.

Semantic work:

- deterministic page-stride integer arithmetic over the reconstructed capability;
- no SHA256 job loop from P9-011;
- a deterministic phase-A workspace signature is also preserved.

## Residency policies

`KEEP_WARM`:

1. reconstruct the 16 MiB runtime capability once before READY;
2. retain it across every phase transition;
3. allocate/touch a 24 MiB phase-A workspace while capability remains resident;
4. release phase-A workspace and perform strided semantic work.

`FAULT_IN`:

1. enter each phase without runtime capability resident;
2. allocate/touch and then release the 24 MiB phase-A workspace;
3. reconstruct the 16 MiB capability from the compressed cold representation;
4. perform identical strided semantic work;
5. unmap capability before the next transition.

The experiment therefore changes both representation/reconstruction shape and semantic-work shape while preserving the same lifetime question.

## Frozen horizons

`H = {2, 4, 8}`.

H=1 is intentionally excluded from the monotonic boundary gate because both policies perform exactly one reconstruction at H=1, making their reconstruction-time difference primarily a measurement-order/noise question rather than a reuse-horizon tax.

Each mode/horizon is repeated twice, with order reversed on repetition 2.

## Typed measurements

For each horizon:

- kernel cgroup-v2 `memory.peak`;
- total capability reconstruction nanoseconds;
- batch wall time as a diagnostic;
- semantic signature;
- OOM events.

The break-even external RAM price is derived only when a real measured tradeoff exists:

`lambda*(H) = reconstruction_tax(H) / peak_memory_saving(H)`

with units ms/MiB.

## Preregistered external-validity gate

PASS requires all of:

- every high-quota run completes with zero kernel OOM;
- semantic signatures match across modes/repetitions;
- compressed source is materially smaller than runtime representation;
- FAULT_IN saves at least 8 MiB of measured kernel peak at H=2,4,8;
- FAULT_IN reconstruction time is higher than KEEP_WARM at H=2,4,8;
- `lambda*(2) < lambda*(4) < lambda*(8)`;
- resource policy grants neither authority nor retry permission.

If any direction reverses, the P9-012 boundary ordering fails this external-validity probe; thresholds are not tuned after observation.

## Interpretation boundary

A PASS would show that the **direction** of the horizon-dependent policy boundary survived one compressed-reconstruction/strided-arithmetic proxy. It would not establish a universal law or application performance result.

Decision candidate:

`HORIZON_DEPENDENT_RESIDENCY_PRICE_BOUNDARY_SURVIVES_A_COMPRESSED_RECONSTRUCTION_AND_STRIDED_ARITHMETIC_SHAPE_IF_QUALIFIED`

Next falsifier: introduce deadline slack and test whether FAULT_IN reconstruction latency can be hidden without recreating the phase-overlap memory peak.

Claim ceiling:
`HOSTED_GITHUB_LINUX_CGROUP_V2_COMPRESSED_RECONSTRUCTION_AND_STRIDED_ARITHMETIC_PROXY_ONLY_NO_UNIVERSAL_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM`
