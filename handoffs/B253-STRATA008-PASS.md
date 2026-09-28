# Bounce Handoff

> **Bounce ID:** B253
> **Status:** COMPLETE / STRATA-008 PASS / TOTAL CAPACITY DECOUPLED AT CURRENT RESOLUTION

## Hosted result

STRATA-008 run `36437651740` completed successfully.

- 24 / 24 trials
- aggregate artifact id `10976142662`
- digest `sha256:8fbdf646686efe6923afd57e78c859b79ceeda9f2124b2c6fd6023de88909186`

## Result

96 MiB anchor:

`80 < K <= 88 MiB`

192 MiB:

`80 < K <= 88 MiB`

Both:

`144 < K+hot <= 152 MiB`

All 4 blocks reproduced the same bracket.

Total scan work doubled and DONTNEED advice calls increased, but instantaneous resident demand remained bounded.

## Empirical bootstrap

20 DONTNEED trials per capacity, 200000 non-parametric resamples, seed 20260928.

Median non-hot-floor shift:

`+0.2421875 MiB`

95% bootstrap interval:

`[-0.001953, +0.250000] MiB`

Do not claim exact equality; claim bounded sub-MiB movement with unchanged knee at the current 8 MiB grid.

## Recorder repair

`systemd-run --version` successfully captured systemd 259 on all four blocks.

## Next action

Freeze a 384 MiB cold-capacity boundary study:

- larger than MemoryMax=320 MiB;
- keep MemoryHigh=160 MiB;
- keep hot anon=64 MiB;
- keep Ubuntu 26.04 and the cadence panel;
- reuse 192 MiB as anchor.

Do not launch during design freeze.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
