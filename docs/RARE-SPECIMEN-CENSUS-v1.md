# Rare specimen census v1

> Existing evidence only. No physical or hosted experiment was launched for this census.

## Canonical inputs and integrity

| Family | Actions run | Trial JSON rows | LOW valid exact-zero | Source result |
|---|---:|---:|---:|---|
| G-A | 36563233676 | 768 | 28/406 | `MEMCG-005G-A-RESULT.md` |
| G-F | 36577573774 | 2,880 | 91/1,374 | `MEMCG-005G-F-RESULT.md` and `MATH-007` |
| G0 Stage A | 36591417373 | 960 | 19/496 | `MEMCG-005G-G0-STAGE-A-RESULT.md` |
| controlled-spawn v2 | 36595481746 | 72 | not applicable | `MEMCG-005G-C-v2-PILOT-RESULT.md` |

The four `gh run download` extracts were read from `/tmp/frl-rare-raw/{ga,gf,g0,spawn}`. Each dataset row carries its source relative path and SHA-256. G0 and spawn have independently archived full raw evidence manifests in `evidence/`; the result documents report byte-identical Drive replicas. G-A and G-F are linked to their Actions run and aggregate artifact digest in their result documents. A fresh reconstruction uses `python3 analysis/rare_specimens.py --raw <download-root>` and writes `analysis/inputs/RARE-SPECIMEN-CENSUS-v1.csv`.

The CSV includes **all 4,680 trial identities**, one row per identity, so incidence denominators are retained. An exact-zero or other rare specimen is selected with the explicit outcome columns. No synthetic rows are introduced from aggregate counts. Rows are unique on `(experiment, run, block, identity)`.

## Field semantics and missingness

- `first_touch_delta_pages` is the natural first fault in G-A/G-F/G0. In spawn it is the constructed terminal target after calibration, observed Q64 primer, and bait touches. These endpoints must be analyzed separately.
- `depth_to_next_q64` in G-A is the reported later-Q64-touch-minus-one **candidate**, not a direct stock read. G0 records exact depth 1 only when the adjacent second touch is Q64; a second zero is encoded as `depth_semantics=at_least_2_second_touch_zero` with numeric depth missing. G-F did not biopsy. Spawn has a terminal pattern index conditional on a primer, a different estimand.
- `pre_current_pages` in natural runs is a pre-fault admission observation; in spawn it is post-migration, before calibration. `pre_current_semantics` prevents accidental pooling.
- G-A used a two-character `70` mapping token. G-F token width is the decimal width of capacity. G0 records the actual token, including padded `08`/`09`. Spawn has no comparable capacity token field in the trial receipt.
- G0 `VmPTE_delta_kib` and `PTE_growth` are first-fault receipts. Spawn PTE growth covers its full measured sequence. Historical G-A/G-F PTE fields are missing, not false.
- Negative accounting deltas are available from G-A biopsy sequences and spawn measured touches. The natural first-fault delta itself is kept separately. A missing negative flag means it was not observed through a comparable sequence.
- THP/mTHP fields come from per-block environment receipts when present. They describe configuration, not a direct huge-page allocation event.
- CPU match, preparation CPU, and stock CPU are trial receipts. Spawn CPU match spans all measured touches; natural runs report the first touch.

## Census findings before modeling

| Stratum | G-A | G-F | G0 |
|---|---:|---:|---:|
| LOW exact-zero | 28/406 | 91/1,374 | 19/496 |
| HIGH zero delta (different selection regime) | 188/362 | 789/1,506 | 261/464 |

G-A depth candidates among 28 exact-zero LOW specimens are 22 at depth1 and six at depths 14, 34, 45, 45, 47, 48. G0's 19 LOW exact-zero specimens include 12 second-touch Q64 receipts and seven second-touch zero receipts (depth at least 2). G0 has five LOW first-fault PTE-growth observations, all Q64, plus three HIGH PTE-growth observations. Spawn has 55 directly observed Q64 primers; all 55 conditional terminal patterns match, while the frozen strict endpoint is 49/72. There are 17 calibration `-17` failures and six negative-only bait failures in spawn; those six still matched the terminal pattern.

## Scope and design cautions

The natural trials are selected by experiment-specific LOW gates. G-A uses CAP70 for biopsy; G-F varies capacity with argv width aliased; G0 breaks the width alias within CAP8/9 and tests CAP10/32. Spawn deliberately constructs a stock phase after a primer. Cross-experiment prediction can be assessed, but a pooled causal capacity or PTE coefficient would conflate these designs. Numeric missing values in the CSV are blank; they must never be interpreted as zero.
