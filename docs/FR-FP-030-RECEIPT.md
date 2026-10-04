# FR-FP-030 Receipt

Status: **PASS / HOSTED PHYSICAL REUSE-LIFECYCLE GOVERNOR PILOT QUALIFIED**

Parent: **FR-FP-029**

- workflow run: 37193948704
- job: 111411800502
- execution head: 9cffccd10b3f96a9f9b72c6779fe2a20245e70e1
- state size: 8 MiB
- frozen reuse count: 17
- reuse ceiling: 0.10
- confidence: 95%
- recent window: 35
- drift alarm threshold: 4

Frozen two-phase trace:

    first 60 opportunities: p(reuse)=0.02
    next 60 opportunities: p(reuse)=0.25

## Physical controls

ALWAYS_WARM
- page-cache residency integral: 960 MiB-opportunity
- warm restores: 17
- cold restores: 0
- total restore latency: 8.044 ms
- storage read bytes: 0

ALWAYS_COLD
- page-cache residency integral: 0 MiB-opportunity
- cold restores: 17
- total restore latency: 1227.717 ms
- storage read bytes: 142,606,336 bytes = 136 MiB

LIFECYCLE_GOVERNOR
- WARM opportunities: 100
- COLD opportunities: 20
- page-cache residency integral: 800 MiB-opportunity
- warm restores: 14
- cold restores: 3
- total restore latency: 34.860 ms
- storage read bytes: 25,165,824 bytes = 24 MiB
- first drift alarm: opportunity 65
- final tier: WARM

Derived reductions in this frozen trace:
- residency integral vs ALWAYS_WARM: 16.67% lower
- cold restores vs ALWAYS_COLD: 82.35% fewer
- storage reads vs ALWAYS_COLD: 82.35% fewer

Every restore verified byte-integrity.

Physical tier separation:
- ALWAYS_WARM reuse-time residency median: 1.0
- ALWAYS_COLD reuse-time residency median: 0.0

Decision:

**CONNECT_REUSE_EVIDENCE_LIFECYCLE_TO_REAL_WARM_COLD_PAGECACHE_ACTUATION**

Theory update:

The reuse-evidence lifecycle is no longer only an analytical policy.

In this hosted physical pilot it successfully:
1. accumulated reuse evidence;
2. qualified COLD;
3. actuated POSIX_FADV_DONTNEED;
4. observed a higher-reuse phase;
5. invalidated stale evidence with the recency alarm;
6. returned the state to WARM;
7. reduced resident page-cache exposure without paying ALWAYS_COLD restore cost.

Next:

Replace the fixed 10% reuse ceiling with the full FR-FP-025/026 risk-aware
decision surface driven by current-run restore calibration and explicit
deadline/memory policy inputs.

Claim ceiling:

**HOSTED_PHYSICAL_TIER_ACTUATION_ON_ONE_SYNTHETIC_TWO_PHASE_REUSE_TRACE_ONLY**
