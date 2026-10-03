# FR-FP-010 Receipt

Status: **PASS / HOSTED PHYSICAL TRAJECTORY RESIDENCY LIFECYCLE QUALIFIED**

Parent: **FR-FP-009**

Final measurement run:
- workflow run: 37144378183
- job: 111265205672
- execution head: b862734ec7e133939a9ac164519b75b9a1b3bd94
- platform: Linux
- kernel: 6.17.0-1022-azure
- page size: 4096 bytes
- GitHub Actions: true

Fixture:
- anonymous private mmap state: 8 MiB
- trajectory steps: 12
- synthetic safe step: 6
- FULL logical peak: 96 MiB
- GATED logical peak: 48 MiB

FULL_TRAJECTORY physical observation:
- baseline VmRSS: 155,396 KiB
- peak/final VmRSS: 253,700 KiB
- VmRSS delta: +98,304 KiB = 96 MiB
- RssAnon delta: +98,304 KiB = 96 MiB
- peak live states: 12
- final live states: 12

GATED_ENDPOINT physical observation:
- baseline VmRSS: 155,396 KiB
- peak VmRSS: 204,548 KiB
- peak VmRSS delta: +49,152 KiB = 48 MiB
- peak RssAnon delta: +49,152 KiB = 48 MiB
- peak live states: 6
- after safe-step close: VmRSS delta +8,192 KiB = 8 MiB
- final VmRSS delta: +8,192 KiB = 8 MiB
- final live states: 1

Physical peak ratio:
- GATED / FULL = 0.5

The physical RSS deltas exactly matched the frozen logical mmap geometry in this
hosted run.

Evidence boundary:
- safe-step semantics are synthetic;
- anonymous mmap allocation, page faults, close/unmap, VmRSS and RssAnon are
  physical hosted-Linux observations.

Decision:

**SEMANTIC_LIFECYCLE_SIGNAL_CAN_REDUCE_HOSTED_PHYSICAL_RESIDENT_FOOTPRINT_WHEN_IT_CLOSES_REAL_MAPPINGS**

Next:

Calibrate live trajectory state count against hosted physical RSS across several
safe-step frontiers to determine whether a reusable resident-byte estimator can
be fitted.

Claim ceiling:

**HOSTED_LINUX_ANONYMOUS_MMAP_RESIDENCY_LIFECYCLE_ONLY**
