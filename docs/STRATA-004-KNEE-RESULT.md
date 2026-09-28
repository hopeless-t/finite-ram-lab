# STRATA-004-KNEE-v1 Result

> **Status:** PASS / TARGETED RESPONSE SURFACE
> **Run:** `36392457515`
> **Launch commit:** `4d22de0570030c987db3e76416c009e67c58341a`
> **Aggregate artifact:** `STRATA-004-KNEE-36392457515`
> **Artifact id:** `10956264153`
> **Artifact digest:** `sha256:8663f4e2d19c760d5483c6cf001c9c55e0d3be8d6f5c51d1698fb4476a59981a`

## Validity

All frozen checks passed: 8 runner blocks, 64 trials, all arms once per block, all trials valid, file cold before every scan, advice success, page-aligned release ranges, content integrity, and no OOM.

## Median response surface

| Arm | high events | max scan MiB | post scan MiB | file residency | advice calls | throughput MiB/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buffered | 5 | 159.92 | 159.86 | 0.875 | 0 | 1598.59 |
| 32 MiB | 0 | 109.86 | 75.86 | 0 | 3 | 1153.84 |
| 48 MiB | 0 | 125.86 | 75.86 | 0 | 2 | 1299.68 |
| 64 MiB | 0 | 141.86 | 75.86 | 0 | 2 | 1031.26 |
| 72 MiB | 0 | 149.86 | 75.86 | 0 | 2 | 2337.31 |
| 80 MiB | 0 | 157.86 | 75.86 | 0 | 2 | 2046.33 |
| 88 MiB | 2 | 159.92 | 75.86 | 0 | 2 | 1007.63 |
| 96 MiB | 5 | 159.92 | 75.86 | 0 | 1 | 1043.70 |

## Finding

On this hosted substrate, the observed pressure-event transition is now bracketed by:

`80 MiB < knee <= 88 MiB`

80 MiB still produced median MemoryHigh events = 0, while 88 MiB produced 2 and 96 MiB reproduced the buffered median of 5.

The transient footprint shows why event count alone is not enough: 80 MiB already reaches ~157.86 MiB against a 160 MiB MemoryHigh threshold. It is therefore a boundary observation, not a safe OSS default.

Hosted timing is noisy and non-monotonic. Throughput values must not be used to select a default from this run.

## Pseudo-Council convergence

- **Systems:** accept 80–88 MiB as the empirical hosted bracket.
- **Statistics:** do not overfit an exact knee from eight blocks; event onset is threshold/substrate dependent.
- **OSS portability:** no default cadence can be inferred from one GitHub-hosted environment.
- **Safety/authority:** Proposal != Decision; research result grants no implementation or default-selection authority.

Consensus: **PASS the targeted refinement; move next to external-validity design rather than finer single-substrate interpolation.**

## Monte Carlo

Deferred. A Monte Carlo model of portability would currently require invented cross-host distributions. First collect at least one materially different hosted substrate or pressure configuration.

## Next research question

Can a cadence be expressed relative to available pressure headroom, rather than as one fixed MiB constant, and does the observed transition move predictably across pressure configurations/substrates?

## Authority boundary

Hosted research only. No local-PC execution. No OSS default cadence authorized.
