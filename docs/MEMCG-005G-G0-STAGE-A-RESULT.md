# MEMCG-005G-G0 Stage A Result

> **Status:** COMPLETE / STAGE-A EXPLORATORY-DIRECTION RESULT
> **Run:** `36591417373`
> **Launch commit:** `1e031ee1a47f07a44e605a73d8e07b2e7b505e6f`
> **Aggregate artifact:** `MEMCG-005G-G0-STAGE-A-36591417373`
> **Aggregate artifact id:** `11043543627`
> **Aggregate ZIP digest:** `sha256:f47a309d4a7351ab3bb7f063011066594647334ec7483cec0e5a574f3fb0a477`

## Execution

- 16 / 16 independent blocks PASS
- 960 / 960 trials valid
- CPU mismatches: 0
- LOW: 496
- HIGH: 464
- LOW first-touch morphology: only Q64 or exact-zero
- nonzero non-Q64 LOW anomalies: 0
- aggregate raw-evidence manifest verification: PASS

## Primary argv-width intervention

Same numeric capacity, different textual representation:

- canonical C8+C9: 3 / 155 exact-zero = **1.9355%**
- padded P8+P9: 2 / 179 = **1.1173%**

Padded minus canonical:

- risk difference: **-0.8182 pp**
- OR: **0.5725**
- pooled Fisher two-sided p: **0.6662**
- block-conditioned CMH p: **0.5030**
- 1,000,000-draw block-conditioned permutation p: **0.6549**

Therefore the prior one-digit/two-digit alias does **not** explain the capacity signal in the direction required by the old confound.

Stage-A interpretation:

`ARGV_WIDTH_EFFECT_NOT_SUPPORTED`

This is stronger than merely saying the alias was unresolved.

## Capacity signal after width control

Matched two-character argv tokens:

- P8+P9 = `08`, `09`: 2 / 179 = **1.1173%**
- H10+H32 = `10`, `32`: 14 / 162 = **8.6420%**

High minus padded:

- risk difference: **+7.5247 pp**
- OR: **8.3716**
- pooled Fisher two-sided p: **0.0012785**
- block-conditioned CMH common OR: **8.839**
- CMH p: **0.00204**
- 1,000,000-draw block-conditioned permutation p: **0.00177**
- Beta(1,1) Monte Carlo P(high > padded): **0.99956**
- posterior risk-difference mean: about **+7.49 pp**
- 95% posterior interval: about **+3.04 to +12.60 pp**

Against canonical C8+C9:

- H10+H32: 14 / 162
- C8+C9: 3 / 155
- Fisher p: **0.01085**
- block-conditioned CMH p: **0.01485**

Stage-A interpretation:

`CAPACITY_SIGNAL_SURVIVES_ARGV_WIDTH_CONTROL`

This does not yet establish a monotone capacity law.

## Gate-selection sensitivity

LOW admission varied somewhat by arm.

The key sensitivity restriction retains only the dominant discrete LOW baseline:

`pre_current_pages in {97,98,99,100}`

This retains 486 / 496 LOW trials.

Within this restricted core:

- canonical: 3 / 151 = 1.99%
- padded: 2 / 176 = 1.14%
- high: 14 / 159 = 8.81%

High vs padded:

- Fisher p: **0.001267**
- block-conditioned CMH OR: **8.833**
- CMH p: **0.00206**

Argv padded vs canonical:

- Fisher p: **0.665**
- block-conditioned CMH p: **0.517**

Therefore the capacity result is not erased by removing unusual LOW baseline values.

## H10 vs H32 heterogeneity candidate

Within valid LOW:

- H10: 11 / 89 = **12.36%**
- H32: 3 / 73 = **4.11%**

H10 vs H32:

- Fisher two-sided p: **0.0907**
- block-conditioned CMH p: **0.0770**
- block-conditioned permutation p: **0.0858**
- Beta posterior P(H10 > H32): about **0.965**

This is a strong follow-up clue, not a Stage-A confirmatory conclusion.

The pooled high signal therefore should not be simplified to “larger capacity monotonically increases capture.”

## PTE receipt result

Across all 960 trials:

- C8 PTE growth: 0 / 160
- P8: 0 / 160
- C9: 0 / 160
- P9: 0 / 160
- H10: 0 / 160
- H32: **8 / 160**

All observed first-fault VmPTE growth events were exactly +4 KiB and all occurred in H32.

H32 vs H10:

- Fisher p: **0.00714**

H32 vs all other arms:

- 8 / 160 vs 0 / 800
- Fisher p: **5.13e-7**

Within LOW:

- VmPTE growth: 5 trials
- exact-zero among those: **0 / 5**
- all 5 were Q64

Within HIGH H32 PTE-growth specimens:

- 3 specimens
- 2 Q64
- 1 exact-zero

This pattern is source-compatible with MATH-009:

a new PTE-page charge can consume the same memcg stock before the data-page charge, and whether the target is still exact-zero depends on residual stock.

The cgroup `memory.stat:pagetables` immediate delta was 0 even for all +4 KiB VmPTE events, validating the decision to treat VmPTE as the primary receipt and memory.stat as corroboration only.

## Two-touch discriminator

There were 19 valid LOW exact-zero first specimens.

First-fault VmPTE growth:

- 0 / 19

Second adjacent touch:

- Q64: 12 / 19 = **63.16%**
- exact-zero again: 7 / 19 = **36.84%**
- second VmPTE growth: 0 / 19

Classification:

- R1_CANDIDATE: **12**
- OTHER: **7**
- R2_CANDIDATE: 0
- PTE_BOUNDARY: 0

Beta(1,1) posterior 95% interval for the R1-candidate fraction is approximately **40.8% to 80.9%**.

Historical G-A depth1 fraction was 22/28 = 78.57%.
A direct exploratory 12/19 vs 22/28 comparison gives Fisher p about **0.324**.

Thus Stage A is compatible with the earlier dominant depth1 population while also revealing a nontrivial residual-depth >1 subgroup.

## THP / mTHP receipt

All 16 blocks reported the same kernel:

`7.0.0-1012-azure`

All 16 reported:

- global THP: `[madvise]`
- 2 MiB: `[inherit]`
- 16/32/64/128/256/512/1024 KiB mTHP sizes: `[never]`

The studied VMA is at most 32 pages = 128 KiB.

Therefore small mTHP is not an active explanation for this Stage-A signal.

## Evidence residency

Full raw manifest:

- schema: `evidence-residency-v1`
- file count: **1936**
- total raw bytes: **4,854,520**
- content-set SHA-256:
  `dd80fb2551833bd001cc27680c6ef3bf3053f7360421667b256b94851ab8798e`

Google Drive COLD replica locator:

`Catfood Lab Evidence/finite-ram-lab/MEMCG-005G-G0/run-36591417373`

COLD contents:

- aggregate ZIP
- all 16 block ZIPs

All 17 Drive files were downloaded back and SHA-256 checked against their GitHub Actions artifact digests.

Result:

`17 / 17 BYTE-IDENTICAL`

The Drive folder is private at verification time.

## Accepted Stage-A conclusions

1. The decimal argv-width confound has been directly broken and does not explain the old signal in the required direction.
2. A strong capacity-associated LOW-state exact-zero signal survives width control.
3. The signal is robust to block conditioning and to restricting the main LOW pre_current mode.
4. CAP32 uniquely creates observed first-fault +4 KiB PTE growth.
5. PTE growth in LOW coincides with Q64, consistent with PTE charge consuming low residual stock before data charge.
6. H10 vs H32 suggests the response is not a simple monotone capacity curve.
7. 12/19 exact-zero specimens exhibit the prospective R1/depth1 signature.
8. Small mTHP is inactive in the observed runner configuration.
9. Raw evidence is now independently preserved and byte-verified in Drive.

## Next

Do **not** blindly extend the original 6-arm design to 32 blocks.

First redesign the next probe to separate:

- the 10-page onset;
- the H32 PTE-boundary suppressor;
- the residual-stock depth distribution.

The controlled-induction track should pre-establish the target PTE table before the Q64 primer so page-table allocation cannot steal the final constructed stock page.
