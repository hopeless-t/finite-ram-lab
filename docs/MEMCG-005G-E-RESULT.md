# MEMCG-005G-E Adaptive Capacity Refinement Result v1

> Status: PASS / UNRESOLVED_TRANSITION
> Run: `36574778995`
> Launch: `272c75dc49fad06d1489d20489332c982fd08c03`
> Aggregate artifact: `11037190120`
> Digest: `sha256:e16586f1f993e9593ef1849049de031bb6e7534c7f2747820eba7e4f8f2e198f`

## Valid REMOTE_LOW capture rates

- CAP8: 1/74 = **1.3514%**
- CAP12: 11/68 = **16.1765%**
- CAP16: 2/74 = **2.7027%**
- CAP19: 9/75 = **12.0000%**
- CAP22: 7/72 = **9.7222%**
- CAP26: 6/81 = **7.4074%**
- CAP32: 7/81 = **8.6420%**
- CAP70: 4/74 = **5.4054%**

CPU mismatches: **0**
Non-{0,Q64} failures: **0**

## Frozen model comparison

AIC:
- CONSTANT: **331.4525**
- HARD_STEP: **328.4386**
- SMOOTH_SIGMOID: **330.4386**
- CATEGORICAL: **327.6955**

Frozen discovery label:

`UNRESOLVED_TRANSITION`

The best hard-step fit is T=9:
- p_low = 1.3514%
- p_high = 8.7619%

The smooth fit collapses to a very sharp transition near the same location:
- c0 ~= 8.87
- w ~= 0.16 pages

However neither model met the frozen discovery gate over alternatives.

## Step-family posterior

Conditional on the hard-step family with uniform T in 9..32:

- median T = 11
- 90% interval = **[9,27]**
- 95% interval = **[9,30]**
- entropy = **3.183 bits**
- maximum one-probe EIG point = **CAP9**

Posterior mass at T=9,10,11,12 is about 20.0% each in this experiment alone.

## Important shape caution

The elevated CAP12 and low CAP16 rates make the observed curve non-monotonic.

A 500,000-draw Monte Carlo under a single shared plateau rate for all CAP12+ arms gives approximately:

`P(range >= observed range) = 0.0569`

Thus the apparent non-monotonicity is interesting but not strong enough to reject a noisy common plateau at conventional levels.

## Accepted conclusion

005G-E does not establish a unique threshold or a smooth transition.

It does reinforce:
- CAP8 as a low-capture regime;
- substantially higher capture rates at many capacities above 8;
- the need for dense sampling at CAP9/CAP10/CAP11 before mechanism claims.

No causal threshold claim.
No K7 inference.
Hosted research only.
