# FR-FP-011 Receipt

Status: **PASS / HOSTED LIVE-STATE TO RSS CALIBRATION QUALIFIED**

Parent: **FR-FP-010**

- workflow run: 37144540667
- job: 111265663625
- execution head: 3a602a12862a8869ba99ff3512213d5567162915

Fixture:
- anonymous private mmap state: 8 MiB
- trajectory length: 12 states
- synthetic safe frontiers: 2 / 4 / 6 / 8 / 10 / 12

Hosted physical observations:

| live-state peak | logical peak | VmRSS delta | RssAnon delta |
| ---: | ---: | ---: | ---: |
| 2 | 16,384 KiB | 16,384 KiB | 16,384 KiB |
| 4 | 32,768 KiB | 32,768 KiB | 32,768 KiB |
| 6 | 49,152 KiB | 49,152 KiB | 49,152 KiB |
| 8 | 65,536 KiB | 65,536 KiB | 65,536 KiB |
| 10 | 81,920 KiB | 81,920 KiB | 81,920 KiB |
| 12 | 98,304 KiB | 98,304 KiB | 98,304 KiB |

VmRSS fit:
- slope: 1.0
- intercept: 0 KiB
- R^2: 1.0
- max absolute residual: 0 KiB

RssAnon fit:
- slope: 1.0
- intercept: 0 KiB
- R^2: 1.0
- max absolute residual: 0 KiB

Median hosted physical cost:
- 8,192 KiB per live trajectory state

All gated arms ended with:
- one live state
- final VmRSS delta: 8,192 KiB
- final RssAnon delta: 8,192 KiB

Decision:

**USE_HOSTED_PHYSICAL_LIVE_STATE_COUNT_AS_A_CALIBRATED_RESIDENT_BYTE_ESTIMATOR_FOR_THIS_MMAP_FIXTURE**

The frozen hosted fixture therefore supports:

    trajectory RSS KiB = 8,192 x live semantic states

with exact agreement in this run.

Evidence boundary:
- semantic frontiers are synthetic;
- mmap allocation, page faults, unmapping, VmRSS and RssAnon are hosted physical.

Next:

Use the calibrated bytes/state value to convert a physical RSS budget into a
semantic hot-state budget and physically spill live-but-not-yet-reclaimable
states to a cold file tier.

Claim ceiling:

**HOSTED_LINUX_ANONYMOUS_MMAP_LIVE_STATE_RSS_CALIBRATION_ONLY**
