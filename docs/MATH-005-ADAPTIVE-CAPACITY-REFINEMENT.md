# MATH-005 — Adaptive Capacity Refinement

Input: MEMCG-005G-D run `36571375684`.

## 1. Post-hoc unrestricted one-step description

Allow one unknown threshold T between observed capacity arms.

Best observed split is:

`CAP8` vs `CAP32 and above`.

Rates:
- CAP8: 2/101 = 1.9802%
- CAP32+: 56/526 = 10.6464%

Two-rate AIC:

`380.3368`

Compared with:
- CONSTANT 388.5996
- LOGISTIC_LINEAR 387.5676
- frozen STEP64 389.0581
- CATEGORICAL 385.1930

Thus the low-capacity one-step description is the best simple descriptive model among these candidates.

For CAP32+ alone, a shared plateau rate fits adequately:
- pooled rate = 10.6464%
- likelihood-ratio heterogeneity p ≈ **0.534**

## 2. Bayesian threshold location under the step family

Assume:
- integer threshold T in 9..70 with uniform prior;
- one Beta(1,1) rate below T;
- one Beta(1,1) rate at/above T.

Posterior probability:

`P(9 <= T <= 32 | data, step model) ≈ 0.98123`

Because there are no tested points inside 9..31, the posterior is almost flat across that interval.

Posterior threshold quantiles:
- 2.5%: 9
- 25%: 15
- 50%: 21
- 75%: 27
- 97.5%: 32

This is a **model-conditional localization**, not proof that a hard step exists.

## 3. Evidence for 8 vs 32+ two-rate model

With Beta(1,1) priors:

Bayes factor two-rate vs one shared rate:

`BF10 ≈ 7.05`

Posterior:
`P(p_32plus > p_8) ≈ 0.9985`

Median rate difference is about **+8.03 percentage points**, with 95% interval roughly **+3.25..+11.69 points**.

## 4. Information-gain next point

Under the current uncertain-threshold step model, calculate expected reduction in threshold entropy for one additional Bernoulli observation at each integer capacity 9..31.

Current threshold entropy:

`H(T) ≈ 4.732 bits`

Maximum one-probe expected information gain occurs at:

`cap_pages = 19`

with nearby 18..21 almost equivalent.

This is expected: the current posterior uncertainty is concentrated across 9..32, so the most informative single point lies near the middle.

## 5. Next experiment principle

Do not jump directly to a single threshold claim.

Use anchors plus an interior refinement grid:

`{8,12,16,19,22,26,32,70}`

Roles:
- 8 = low-rate anchor;
- 32 = first known high-rate point;
- 70 = independent enriched plateau anchor;
- 12/16/19/22/26 = threshold-shape refinement;
- 19 = current maximum-EIG point.

The successor should compare:
- hard-step family with unknown T;
- smooth sigmoid with center c0 and width w;
- monotonic isotonic shape;
- categorical shape.

The scientific target becomes estimating:
- transition location c0/T;
- transition width w;
- low plateau;
- high plateau.

## 6. Why this matters for the original 1.6%

If CAP8 remains on the low plateau while capacities above an unknown transition enter a ~10% plateau, then the original ~1.6% is not a universal irreducible error rate.

It is a state probability conditional on a particular footprint regime.

The mechanistic question then becomes:

`what kernel-visible consequence of mapping capacity moves the system between these regimes?`

No causal answer is claimed yet.
