# B475 — Coverage-Aware q Governor v1

Status: **SOFTWARE GOVERNOR WITH EXPLICIT RANK COVERAGE CONTRACT**.

## 1. Goal

B470's `observed_upper` mode attached no quantitative predictive coverage to the
peak threshold.

B471-B474 showed why that matters: empirical maxima moved as more fresh-process
samples were collected.

B475 replaces the vague risk label with explicit calibration metadata.

## 2. Calibrated q points

### q=1

- pooled empirical max = 67,117,056 B
- comparable samples = 20
- one-step rank-max coverage floor = 20/21 ~= 95.238%

### q=2

- pooled empirical max = 67,194,880 B
- comparable samples = 19
- coverage floor = 19/20 = 95%

### q=4

- pooled empirical max = 71,389,184 B
- comparable samples = 19
- coverage floor = 95%

### q=7

- pooled empirical max = 71,544,832 B
- comparable samples = 19
- coverage floor = 95%

All coverage statements are conditional on future observations being exchangeable
with the pooled comparable calibration observations.

## 3. Selection rule

Given:

- peak budget B;
- minimum required rank coverage p;

choose the q with the lowest balanced-sweep median latency such that:

```text
empirical_max_peak(q) <= B
rank_coverage_floor(q) >= p
```

The latency ordering remains sourced from the balanced B469 Pareto sweep.

No memory/latency weighted scalar is introduced.

## 4. 95% policy breakpoints

At minimum rank coverage 0.95:

```text
budget 67,117,056 B -> q=1
budget 67,194,880 B -> q=2
budget 71,389,184 B -> q=4
budget 71,544,832 B -> q=7
```

The q2 transition now requires:

`77,824 B`

of empirical-max headroom above q1.

That is larger than B470's old median/observed-upper transition because the
calibration set exposed additional tail observations.

## 5. Decision receipt

A v1 decision reports:

- selected q;
- declared peak budget;
- minimum rank coverage;
- selected pooled empirical maximum;
- selected sample count;
- selected rank coverage floor;
- balanced-sweep median latency;
- exchangeability assumption.

Thus the risk model is visible to the caller.

## 6. What 99% means

At minimum rank coverage 0.99, no q currently qualifies.

Each q would need at least:

`n=99`

comparable observations for a sample-max rank floor of 99%.

The governor fails closed rather than silently relabeling 95% evidence as 99%.

## 7. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_COVERAGE_AWARE_GOVERNOR_V1**

This is not a hard real-time or worst-case memory guarantee.

Environment or workload drift invalidates the exchangeability premise and should
open a recalibration lane.

## 8. Next

B476 should dogfood v1 at the calibrated 95% breakpoints.

Any new exceedance is expected to be possible under the declared risk contract
and must be recorded as a calibration event, not hidden.

A later governor can use drift detection to distinguish ordinary tail exceedance
from loss of exchangeability.
