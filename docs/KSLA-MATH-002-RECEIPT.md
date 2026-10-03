# KSLA-MATH-002 — Bounded Idiocy Qualification Receipt

Status: **PASS / ANALYTIC + MATCHED MONTE CARLO VALIDATED**

## Qualification

- workflow run: 37102291358
- job: 111144043704
- execution head: 84e5a9e0d6cc1c2b58c6a4193cd225bc223acfdf
- targeted tests: 7/7 PASS
- artifact ID: 11266152904
- artifact ZIP SHA256: 066556c413712080c99b5a5bd35a4219c8991d15be35b3a7786e28f58b6d3743
- spec SHA256: dd47cb2e4e33ee4093472f440c1d53659264442d79c4ef14f8a61f4fda990ca5
- result SHA256: 02bcb6582c4bd9d8ca45446d5fe7d50903e938ef6fcf94da4071db2896658d12

## Frozen toy economics

- blind-state probability: 0.15
- expert cost: 8
- idiot cost: 1
- hard budget: 16
- direct resource price lambda: 0.39
- expert reward: 8 normal / 0 blind
- idiot reward PMF:
  - 0 with probability 0.80
  - 2 with probability 0.17
  - 20 with probability 0.03

## Analytic result

Hard-budget maximum expected progress:

- expert only: 6.8
- pure idiot, 16 proposals: 8.8871392423
- 1 expert + 8 idiots: 9.8393790153

Therefore the mixed portfolio beats both pure extremes on expected progress.

With priced utility:

`U = E[progress] - 0.39 * cost`

the optimum is:

`1 expert + 3 idiots`

with:

- cost: 11
- expected progress: 8.0729183
- analytic utility: 3.7829183

The optimum leaves 5 cost units unused, demonstrating bounded rather than
maximal idiocy.

## Matched Monte Carlo

Episodes: 200,000.

All candidate policies use the same latent regime draw and the same ordered
idiot proposal tape per episode.

Maximum absolute analytic-vs-Monte-Carlo expected-progress error:

`0.0190067423`

Selected empirical utilities:

| policy | mean progress | cost | utility |
|---|---:|---:|---:|
| expert only | 6.78996 | 8 | 3.66996 |
| **1 expert + 3 idiots** | **8.05827** | 11 | **3.76827** |
| 1 expert + 8 idiots | 9.82078 | 16 | 3.58078 |
| 16 idiots | 8.87427 | 16 | 2.63427 |

Thus the matched simulation preserves the analytic conclusion:

`pure expert < bounded idiocy > pure idiot`

under the frozen resource price.

## Negative control

With no blind state and an idiot family whose best possible reward is below the
expert reward, the first idiot adds exactly zero progress.

At positive cost it must be rejected.

Therefore this experiment does not encode "randomness is always beneficial".

The supported toy statement is:

`complementary / upper-tail idiocy can be beneficial when externally verified and resource-priced`.

## Mathematical criterion

For e expert and k idiot proposals:

`E[G_e,k] = integral (1 - F_E(y)^e F_I(y)^k) dy`

Replacing one expert with one idiot has progress value:

`integral F_E(y)^(e-1) F_I(y)^k (F_E(y)-F_I(y)) dy`.

In the simple blind-spot heavy-tail model, the marginal value of idiot k+1 is:

`p(1-p)^k [H-(1-q)g]`.

This decays geometrically, supplying the mathematical reason for a bounded
idiot allocation.

## Claim ceiling

**TOY_ANALYTIC_AND_MATCHED_MONTE_CARLO_BOUNDED_IDIOCY_ONLY**
