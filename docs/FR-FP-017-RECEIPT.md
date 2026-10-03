# FR-FP-017 Receipt

Status: **PASS / HOSTED 8 MiB COLD RESTORE TEMPORAL TRACE QUALIFIED**

Parent: **FR-FP-016**

- workflow run: 37152732983
- job: 111289757589
- execution head: b4dee783059f97cd91adf87b17afe11de799ba23
- paired blocks: 48

WARM control:
- p50: 0.921 ms
- p95: 1.063 ms
- max: 1.104 ms
- CV: 0.078

COLD:
- p50: 3.729 ms
- p90: 26.663 ms
- p95: 27.131 ms
- p99/max: 42.411 ms
- CV: 1.042
- 25 ms miss rate: 16.67%
- 50 ms miss rate: 0%
- 100 ms miss rate: 0%

Temporal observations:
- lag-1 autocorrelation: -0.240
- lag-2 autocorrelation: -0.391
- lag-4 autocorrelation: 0.277
- >25 ms misses: 8
- >25 ms max consecutive run: 1
- every >25 ms miss was isolated in this trace

Contiguous 12-block COLD epochs:
- epoch 1: p50 3.655 ms / p95 42.411 ms
- epoch 2: p50 4.010 ms / p95 34.160 ms
- epoch 3: p50 3.612 ms / p95 26.641 ms
- epoch 4: p50 3.729 ms / p95 26.442 ms

Paired result:
- COLD slower than WARM: 48/48 pairs
- median COLD/WARM ratio: 4.136x
- max paired ratio: 44.646x

Theory update:

The long trace confirms a heavy COLD tail, but does not show simple contiguous
slow bursts. The 25 ms exceedances were isolated and the short-lag correlations
include negative values.

Do not promote a two-state slow-burst HMM yet.

Next:
- freeze this exact trace;
- preserve its marginal latency distribution;
- shuffle only temporal order with Monte Carlo;
- test whether lag correlations, isolated exceedances and epoch drift differ
  materially from an iid-order null.

Decision:

**TEST_TEMPORAL_ORDER_AGAINST_A_SHUFFLED_MARGINAL_NULL_BEFORE_FITTING_LATENT_IO_STATES**

Claim ceiling:

**HOSTED_8MIB_COLD_RESTORE_TEMPORAL_TRACE_PILOT_ONLY**
