# MEMCG-005G-A Early-Transient + Residual-Stock Biopsy Result v1

> **Status:** PASS / INCONCLUSIVE_EARLY_TRANSIENT / BIOPSY_SIGNAL
> **Run:** `36563233676`
> **Launch:** `085ff36e9fbc86cd634bf1795322be9eef1b5544`
> **Aggregate artifact:** `11030304423`
> **Digest:** `sha256:af41add578f237d02c27a5513cfb5c45201728cd6d0d40d497c8b18135558299`

## Primary preregistered decision

`INCONCLUSIVE`

Among valid REMOTE_LOW probes:

### EARLY identity 0..7
- n = **102**
- failures = **9**
- failure rate = **8.8235%**
- all failures were zero-delta

### STEADY identity 8..31
- n = **304**
- failures = **19**
- failure rate = **6.25%**
- all failures were zero-delta

Risk difference:

`+2.5735 percentage points`

One-sided Fisher EARLY > STEADY:

- odds ratio = **1.4516**
- p = **0.2484**

Bayes factor, two independent rates vs one shared rate:

`BF10 = 0.1130`

Under the frozen Beta(1,1) comparison this favors the shared-rate model by about 8.85:1.

Therefore the historical concentration of all failures in identity0..7 was **not independently confirmed**.

## Important cross-experiment shift

MEMCG-005F REMOTE_LOW:
- 2/123 failure = **1.626%**

MEMCG-005G-A REMOTE_LOW:
- 28/406 failure = **6.897%**

Exploratory two-sided Fisher comparison gives approximately:

`p = 0.0253`

This cross-experiment comparison was not preregistered and cannot identify cause.

A material implementation/environment difference is that MEMCG-005G-A started the unchanged worker with `--max-pages 70` rather than the historical `--max-pages 8`, to permit biopsy after a failed first touch. MEMCG-005G-A also used 24 independent hosted jobs rather than 4.

This must be controlled before interpreting the higher failure rate mechanistically.

## Failure biopsy

All 28 valid REMOTE_LOW first-touch zero failures reached a later Q64 by touch65.

No biopsy was censored >64.

Residual-depth candidates:

`[34,1,1,45,1,1,1,47,1,1,1,1,1,1,1,1,1,1,1,45,1,1,1,1,1,48,14,1]`

Histogram:

- depth1: **22/28 = 78.57%**
- depth14: 1
- depth34: 1
- depth45: 2
- depth47: 1
- depth48: 1

Beta(1,1) 95% posterior interval for the depth1 fraction:

approximately **60.3% to 89.7%**.

The data therefore expose at least an apparent dominant one-page residual phenotype plus a much smaller deep-residual tail.

## Exploratory phase × phenotype note

Among failures:

- EARLY deep (>1) phenotype: **4/9**
- STEADY deep (>1) phenotype: **2/19**

Exploratory one-sided Fisher p is approximately **0.064**.

This is not confirmatory but suggests that startup phase may affect **failure depth phenotype** more than failure incidence.

## Biopsy estimator caveat

`residual_depth_candidate = first later Q64 touch index - 1`

is source-consistent, not a literal direct stock read.

At least one deep biopsy sequence contained an intermediate `memory.current` delta of -2 pages before later Q64. Therefore asynchronous charge/uncharge activity can occur during biopsy, and the candidate depth must not be treated as exact causal stock occupancy without further control.

## Accepted conclusions

1. The frozen EARLY 0..7 failure-incidence hypothesis was not confirmed.
2. REMOTE_LOW failure is reproducible at a nonzero rate.
3. Biopsy converted 28 first-touch zero failures into structured recovery-depth observations.
4. A dominant depth1 phenotype was observed.
5. A minority deep phenotype 14..48 was observed.
6. The increase from 005F to 005G-A requires a footprint/runner control before being attributed to hidden-state biology.

## Next

MEMCG-005G-B controls the biopsy-capacity perturbation:

`CAP8 vs CAP70`

within the same hosted runner and alternating order.

No K7 inference.
Hosted research only.
