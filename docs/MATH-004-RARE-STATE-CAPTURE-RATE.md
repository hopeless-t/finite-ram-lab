# MATH-004 — Rare-State Capture-Rate Model

Input: MEMCG-005G-B run `36568284433`.

## Observed capture rates

- CAP8: 3/240 = 1.25%
- CAP70: 26/249 = 10.4418%

Using independent Beta(1,1) priors:

- CAP8 posterior: Beta(4,238)
- CAP70 posterior: Beta(27,224)

Posterior summaries:

### CAP8
- median ≈ 1.521%
- 95% interval ≈ 0.454%..3.594%

### CAP70
- median ≈ 10.651%
- 95% interval ≈ 7.235%..14.871%

CAP70-CAP8:
- median ≈ +9.03 percentage points
- 95% interval ≈ +5.15..+13.46 points

Risk ratio CAP70/CAP8:
- median ≈ 6.99
- 95% interval ≈ 2.72..24.41

`P(p70 > p8) ≈ 0.999998`

## Posterior-predictive specimen capture

For posterior Beta(a,b):

`P(at least one capture in n) = 1 - B(a,b+n)/B(a,b)`

Required future valid REMOTE_LOW probes:

| target >=1 specimen | CAP8 | CAP70 |
| ---: | ---: | ---: |
| 50% | 46 | 7 |
| 90% | 187 | 22 |
| 95% | 267 | 28 |
| 99% | 518 | 45 |
| 99.9% | 1108 | 70 |

Thus CAP70 reduces the posterior-predictive 95% specimen requirement from about 267 valid LOW probes to about 28.

## Scientific consequence

The research object is no longer only a passive rare event.

Mapping capacity is now an experimentally controlled enrichment parameter:

`p_capture = f(mapping_capacity, CPU/history/state)`

The next question is to map that function and then determine which residual-depth phenotype is enriched.

No claim is made that the effect occurs at a 64-page threshold.
