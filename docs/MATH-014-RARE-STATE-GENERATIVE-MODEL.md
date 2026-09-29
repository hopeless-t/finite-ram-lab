# MATH-014 — Rare-state generative model from existing specimens

> **Status:** retrospective model comparison. No physical run or hosted compute launch.  
> **Inputs:** canonical census v1; G-A, G-F, G0 Stage A, and controlled-spawn v2 raw trial JSON; prior MATH-003/009/011/012/013 and result documents.  
> **Code/output:** `analysis/rare_state_models.py`, `analysis/inputs/RARE-STATE-MODEL-COMPARISON-v1.json`.

Rebuild after `python -m pip install -e '.[analysis]'` with `python analysis/rare_state_models.py`. The script fixes Monte Carlo seeds and writes the complete numeric output as JSON. The census builder requires the four previously downloaded Actions artifact directories and verifies the G0/spawn full raw manifests before reading trial rows.

## Search → atomic decomposition → pseudo-Council → Monte Carlo

The evidence search recovered 4,680 raw trial identities from the four Actions runs. G0 and spawn raw files were rechecked against their archived full manifests: 1,936/1,936 and 152/152 path, byte-length, and SHA-256 matches. G-F's result count of 93 failures includes two nonzero anomalies; the target **exact-zero** count is 91. The census retains every candidate in the denominator and leaves unavailable historical PTE receipts blank.

The mechanism was decomposed into (a) admission to the LOW stratum, (b) the unobserved residual per-CPU memcg stock before a target fault, (c) possible PTE allocation before the data charge, (d) the fault's zero/Q64/other accounting emission, (e) a later Q64 biopsy or constructed terminal pattern, and (f) asynchronous negative uncharge/drain emissions. This decomposition keeps `pre_current`, stock, and accounting observations distinct.

The pseudo-Council tested four objections before modeling: a statistician required block-held-out validation and block resampling; a VM reviewer treated VmPTE as a receipt rather than proof of charge order; a measurement reviewer kept negative deltas in the frozen strict endpoint; and a falsification reviewer required the natural and primer-conditioned cohorts to have separate selection likelihoods. We therefore fit simple incidence first and allow the latent model to fail on prediction.

## Natural LOW exact-zero incidence

G-F provides 1,374 valid LOW candidates and 91 exact zeros; G0 provides 496 and 19. G-A provides 406 and 28, but its CAP70 biopsy setup and different runner/batch design make it a phenotype and depth validation cohort, not part of the G-F/G0 capacity fit. HIGH is a separate gate and is not pooled with LOW.

| Check | Exact-zero counts | Result |
|---|---:|---|
| G-F CAP8+9 vs CAP10+11+12+32 | 14/452 vs 77/922 | RD 5.25 pp; Fisher p=0.000124; block bootstrap RD 95% interval 2.90–7.52 pp |
| G0 CAP8/9 vs CAP10/32 | 5/334 vs 14/162 | RD 7.14 pp; Fisher p=0.000228; block bootstrap 3.49–11.25 pp |
| G-F CAP9 vs CAP10 | 7/226 vs 21/243 | Fisher p=0.0115, exploratory adjacent contrast |
| G0 width-matched padded 08/09 vs 10/32 | 2/179 vs 14/162 | Fisher p=0.00128; retained from G0 result |
| G0 canonical 8/9 vs padded 08/09 | 3/155 vs 2/179 | Fisher p=0.666; no directionally required width effect |

Across G-F/G0, a block-conditioned CMH common OR is 3.22 (p=2.73e-6). A 20,000-draw within-block permutation gave two-sided p≈5.0e-5. These are association tests under the observed LOW admission process, not a universal causal capacity coefficient.

### Ordered model ladder

The comparison cohort is the 1,870 valid LOW G-F/G0 trials. Five folds hold out entire experiment-specific blocks. Log loss is per held-out trial; lower is better. AIC/BIC for the random-effect and mixture fits are exploratory marginal-likelihood summaries and must not be read as proof of latent-state identity.

| Step | Model | AIC | BIC | Block-held-out log loss |
|---:|---|---:|---:|---:|
| 1 | Constant incidence | 838.71 | 844.24 | 0.2240 |
| 1 | CAP10+ step | 808.04 | 819.11 | **0.2155** |
| 2 | Block-conditioned effect | CMH OR 3.22 | — | within-block permutation p≈5.0e-5 |
| 3 | Experiment × step, pre-current, padded-token interaction model | 803.06 | 836.26 | 0.2310 |
| 4 | Gaussian block-intercept hierarchical logistic | 810.69 | 838.36 | 0.2171 |
| 5 | Two-regime latent block mixture | 811.58 | 844.78 | 0.2172 |

The richer interaction fit improves in-sample AIC over a step, but loses held-out predictive accuracy. The hierarchical fit estimates block-intercept SD 0.34 on the log-odds scale. The two-regime mixture puts about 90.5% mass in a rich regime and drives the other regime's base log-odds to about -13.2, a near-degenerate representation. Neither beats the simple step in block-held-out scoring. The latent mixture is **not identified as physical residual stock** by binary incidence alone.

The interaction model's posterior predictive Monte Carlo generated 10,000 replicated block event-count variances. Observed variance was 2.36, simulation median 1.81, two-sided tail probability 0.19. This check does not establish a need for additional block heterogeneity, though it has limited power for rare tails.

## Depth1 versus deeper state

G-A biopsies: 22/28 depth1 and six candidate depths 14, 34, 45, 45, 47, 48. G0's adjacent-touch discriminator: 12/19 exact depth1 and seven **at least depth2**; G0 did not continue until Q64 for those seven, so their numeric depth is missing. The exploratory G-A/G0 depth1 fraction comparison has Fisher p=0.324. On G-A's exact depth candidates, a single geometric law has AIC 178.51/BIC 179.85. A depth1 point mass plus shifted geometric deep tail has AIC 88.53/BIC 91.20, with fitted depth1 weight 0.786 (Beta posterior 95% interval 0.603–0.897). The fitted single geometric law assigns depth1 probability 0.1098, giving a plug-in binomial tail probability of 1.5e-16 for at least 22 depth1 specimens among 28. MATH-003 reached the same qualitative conclusion with a different deep-tail specification. This supports a spike-and-tail **phenotype**; it does not identify an exact stock occupancy distribution because asynchronous accounting occurred during at least one G-A biopsy.

## PTE, pre-current, and observation contamination

G0 has five LOW first-fault `VmPTE +4 KiB` trials; all five emitted Q64, versus 19 exact zeros among 491 LOW trials without growth. The within-LOW Fisher p is 1.0 and a Beta(1,1) Monte Carlo gives only about 0.22 probability that the PTE-growth group's exact-zero rate is lower. This small, capacity-confounded subset is **compatible with** PTE stock consumption but does not establish a statistical suppression effect. One HIGH PTE-growth trial was exact-zero, so a deterministic universal veto is rejected. G-A/G-F have no per-trial VmPTE receipt.

In G-F's dominant `pre_current ∈ {97,98,99,100}` range, 88/1,351 exact zeros remain. Adjusting for CAP10+, the within-core OR per pre-current page is about 1.77 (p=0.00026); with block fixed effects it is about 1.56 (p=0.010). In G0, the pre-current coefficient is imprecise (p=0.80 over all LOW; p=0.45 in the 97–100 core). Therefore `pre_current` is not merely a selection gate in G-F's measured population, but transport of that predictor to G0 is unresolved. Its coarse cgroup total is not a direct stock read. The capacity signal survives G0's 97–100 restriction (5/327 vs 14/159).

Controlled-spawn v2 yielded 55 directly observed Q64 primers among 72 frozen identities. All 55 primer-qualified terminal patterns matched b62/b63/b64 predictions; the frozen strict endpoint remains **49/72** because 17 calibration OTHER deltas and six negative-only bait deltas count as failures. The six negative bait trials still had the predicted terminal phase. Twenty-three identities had a negative measured sequence event. Treating negative `memory.current` steps as stock consumption would misclassify them; a drain/uncharge emission is a plausible observation contaminant, while the exact source of `-17` is unresolved. A Beta posterior one-sided 95% lower bound for the 55/55 conditional match rate is about 94.8%, below a 95% reliability certification.

G0 environment receipts reported THP `[madvise]`, 2 MiB `[inherit]`, and 16–1024 KiB mTHP sizes `[never]` on all 16 blocks. The studied natural VMA is at most 128 KiB. Small mTHP is not an active explanation for G0's observed split. Historical THP receipt gaps remain missing in the table.

## Minimal generative account

Let (R_t) be unobserved charged pages remaining in a CPU-local batch before a measured data fault. Let (P_t\in\{0,1\}) mark a PTE-page allocation that consumes a stock page first, and (U_t\ge0) an asynchronous uncharge. A schematic transition is

\[
R_t' = R_t-P_t,\qquad
D_t = \begin{cases}0,&R_t'>0\\64,&R_t'=0\text{ and a new batch is charged}\end{cases}-U_t+\epsilon_t.
\]

This is a **mechanism sketch**, not a fitted causal kernel equation. A natural trial samples an unknown (R_0) distribution conditional on experiment, block, capacity, admission gate, and runner state. A primer-qualified spawn observes a Q64 reset, then consumes a controlled number of pages with PTE growth suppressed by preconditioning. The same stock-transition arithmetic explains the conditional b62/b63/b64 terminal sequence and can accommodate natural depth1/deep candidates, but the natural initial-state distribution and selection process are not identified by the spawn cohort. Thus one transition mechanism is supported; one pooled incidence-generating probability model is not.

## Verdicts

| Status | Claim |
|---|---|
| **確定** | Raw census identities, 91 G-F exact zeros, 19 G0 LOW exact zeros, 22/28 G-A depth1 candidates, 12/19 G0 adjacent depth1, 49/72 frozen spawn strict successes and 55/55 conditional matches. |
| **支持** | A CAP10-neighborhood association persists after G0 width control and block conditioning; a depth1 spike plus deeper tail; Q64-anchored stock-phase arithmetic; negative deltas contaminate `memory.current` outcome classification. |
| **未解決** | Physical cause of the capacity association; PTE suppression magnitude; whether G-F pre-current prediction transports to G0; exact `-17` source; natural starting residual-state distribution; reliability beyond this pilot. |
| **棄却** | Decimal argv width as the required explanation of G0 capacity split; a universal deterministic PTE-growth veto; a literal all-failures-are-exact-zero G-F endpoint; a single geometric law for G-A depth; replacing the frozen 49/72 endpoint with conditional 55/55. |

No K7 or external deployment conclusion follows. No new physical experiment was executed.
