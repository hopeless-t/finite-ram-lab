# MATH-010 — Minimal Alias-Breaker Monte Carlo Calibration

> **Status:** DESIGN CALIBRATION
> **Target:** MEMCG-005G-G0 Minimal Argv/PTE Alias Breaker v1
> **No run launched.**

## 1. Planning rates

Use MEMCG-005G-F exact-zero rates only as planning inputs:

- canonical low CAP8+CAP9: 15/452 = 3.3186%
- high CAP10+CAP11+CAP12+CAP32: 78/922 = 8.4599%
- valid REMOTE_LOW admission: approximately 47.7%

The new direct argv contrast pools:

- canonical low: C8+C9
- padded low: P8+P9

Each arm receives 10 raw candidates/block.

Therefore each pooled side receives:

`20 * blocks`

raw candidates.

## 2. Simulated argv-causal world

Planning alternative:

- canonical low exact-zero probability = 0.033186
- padded low exact-zero probability = 0.084599

For every simulated candidate:

1. sample valid REMOTE_LOW admission with p=0.477;
2. conditional on admission, sample ZERO_CAPTURE;
3. compare padded vs canonical using two-sided Fisher exact test;
4. count success only when padded rate > canonical rate and p < .05.

10,000 Monte Carlo repetitions per scale.

## 3. Results

| blocks | raw total for six-arm experiment | P(correct direction) | P(correct direction AND Fisher p<.05) |
| ---: | ---: | ---: | ---: |
| 16 | 960 | 97.22% | 42.66% |
| 24 | 1440 | 99.21% | 62.59% |
| 32 | 1920 | 99.76% | 75.83% |
| 40 | 2400 | 99.91% | 85.91% |
| 48 | 2880 | 99.96% | 90.69% |

The same contrast scale applies approximately to a capacity-survival comparison if padded CAP8/9 remains in the low regime while H10/H32 remains in the high regime.

## 4. Null calibration

Under no argv-width effect:

- canonical low p = 0.033186
- padded low p = 0.033186

Using the same rule (two-sided Fisher p<.05 AND padded direction), empirical false-positive frequency was about 1.7-1.9% across the tested scales.

This is expected to be below 2.5% because the decision additionally requires one direction.

## 5. Recommended multi-bounce ladder

### Stage A — 16 blocks / 960 candidates

Purpose:

- verify raw token `08/09` arrives and parses as 8/9;
- verify VmPTE pre/post receipt completeness;
- estimate the direction of the same-capacity token intervention;
- audit nonzero morphologies.

Do not treat failure to reach p<.05 at Stage A as evidence against argv.

### Stage B — cumulative 32 blocks / 1920 candidates

Purpose:

- main discovery-scale alias breaker;
- about 75.8% planning power for a G-F-sized argv effect;
- direction recovery about 99.8%.

### Stage C — cumulative 48 blocks / 2880 candidates

Purpose:

- stronger closure if Stage B remains scientifically important but not decisive;
- about 90.7% planning power for the G-F-sized argv effect.

## 6. Sequential inference caution

The staged ladder is primarily a resource-control mechanism.

Do not repeatedly inspect ordinary p-values and then present a stopped run as fixed-N confirmatory inference.

Acceptable options:

1. label Stage A/B reads exploratory and reserve fixed-N confirmatory interpretation for a preregistered terminal stage; or
2. freeze a formal group-sequential error-spending rule before launch.

For current research, option 1 is simpler.

## 7. Council result

A 16-block pilot has high probability of getting the effect direction right if the old gap is real, while limiting hosted compute.

A cumulative 48-block ceiling reaches about 90% planning power without exceeding the previous G-F scale of 48 blocks / 2880 candidates.

Recommended route:

`16 -> 32 -> 48 only as needed`

with Human approval at each hosted-compute boundary.

No local-PC execution.
