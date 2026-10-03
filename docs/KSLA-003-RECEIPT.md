# KSLA-003 — Real-State Bounded Idiocy Qualification Receipt

Status: **PASS / REAL-STATE FINITE-VIEW BOUNDED IDIOCY VALIDATED**

## Qualification

- workflow run: 37103639999
- job: 111147858232
- execution head: 8dc02d4fcd693537a5e92f84faec9b352e05d32d
- targeted tests: 7/7 PASS
- artifact ID: 11266809713
- artifact ZIP SHA256: 4e8dbdc294067d8718549c852b3a0aa2068358d13e45b55c427bcf0ae2e005fb
- spec SHA256: 67f239fdde488d06b7f7242c77df74a8c94e49ddb0901491e22905e1174844d3
- result SHA256: 346437c5cc596e63f370397e460cd104d0f60313d34148265f01a7915460ca9b

## Frozen experiment

- episodes: 512 matched episodes
- dimension: 256
- active coordinates: 48
- expert resident cache: 8 coordinates per expert lane
- action steps: {-4,-2,-1,+1,+2,+4}
- global refresh cost: 1536 abstract evaluations
- max rounds: 500

## Frozen results

| policy | success | mean rounds | mean work | refresh work | resident coords |
|---|---:|---:|---:|---:|---:|
| EXPERT_HEAVY | 512/512 | 46.083984375 | 9032.0625 | 4608 | 16 |
| EXPERT_ONLY | 512/512 | 77.9921875 | 12959.625 | 9216 | 8 |
| FIXED_LOW | 512/512 | 75.513671875 | 12416.197265625 | 8565 | 8 |
| FIXED_HIGH | 512/512 | 70.86328125 | 10685.34375 | 6717 | 8 |
| STALL_ADAPTIVE | 512/512 | 73.255859375 | 8169.34375 | 3636 | 8 |
| IDIOT_ONLY | 384/512 | 414.21875 | 6627.5 | 0 | 0 |

## Main result

Compared with EXPERT_HEAVY, STALL_ADAPTIVE preserves 512/512 success while:

- reducing mean work by 9.5517%;
- reducing global-refresh work by 21.09375%;
- using half the expert resident coordinates;
- discovering about 31 cold coordinates per episode through ignorant proposals.

The cost is serial depth:

- EXPERT_HEAVY: 46.084 rounds;
- STALL_ADAPTIVE: 73.256 rounds.

Therefore this is a finite-resource trade, not a universal speed win.

## Resource-price frontier

For:

`J = mean_work_cost + lambda_round * mean_rounds`

the break-even between STALL_ADAPTIVE and EXPERT_HEAVY is:

`lambda_round ~= 31.7504 work units per serial round`.

Below that latency price, STALL_ADAPTIVE is cheaper.

Above it, EXPERT_HEAVY is worth the additional work and residency.

## Negative controls

IDIOT_ONLY uses less abstract work but fails the frozen reliability floor:

- success: 384/512 = 75%.

Fixed idiocy also loses to stall-gated idiocy on work:

- FIXED_LOW: 12416.20
- FIXED_HIGH: 10685.34
- STALL_ADAPTIVE: 8169.34

So the supported conclusion is not "more stupidity is better".

It is:

`inject cheap ignorance only at expert blind / stall boundaries`.

## Reproducibility repairs

The first two workflow attempts correctly failed because the GitHub
implementation did not exactly preserve the prototype experiment identity.

Repair 1 restored the original SHA256 draw-domain names.

Repair 2 restored the original expert tie-break rule.

No policy threshold, workload size, expected result, reliability criterion, or
cost coefficient was relaxed.

This reinforces:

`random-stream identity + decision tie-break identity are part of the frozen experimental state`.

## Claim ceiling

**SYNTHETIC_REAL_STATE_FINITE_VIEW_EXPERIMENT_ONLY**
