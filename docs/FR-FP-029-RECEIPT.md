# FR-FP-029 Receipt

Status: **PASS / SYNTHETIC REUSE DRIFT-ALARM PARETO FRONTIER QUALIFIED**

Parent: **FR-FP-028**

- workflow run: 37193430533
- job: 111410230780
- execution head: 4db19ae69533670599fa0dc941df9847b202ae94
- replicates: 10,000
- reuse ceiling: 0.10
- recent window: 35 observations
- alarm thresholds: 3 / 4 / 5 / 6 / 7 / 8

Stable p=0.02 false-revocation rates:
- cumulative exact UCB: 2.60%
- k=3: 9.27%
- k=4: 1.94%
- k=5: 0.38%
- k=6: 0.03%
- k=7: 0%
- k=8: 0%

Weak drift p=0.02 -> 0.15:
- cumulative: detection 93.52%, median delay 14
- k=3: 99.33%, delay 17
- k=4: 95.87%, delay 23
- k=5: 87.89%, delay 29
- k=6: 72.94%, delay 33
- k=7: 53.66%, delay 35
- k=8: 34.59%, delay 37

Moderate drift p=0.25 is detected by k=3..6 at >=99.1%.

Strong drift p=0.50 is detected by every tested alarm threshold.

Qualified Pareto thresholds:
- 3 / 4 / 5 / 6 / 7

Interpretation:

There is no universal drift-alarm winner.

A lower threshold buys coverage and faster detection at the cost of false
revocation.

A higher threshold preserves qualified evidence but can miss or delay weak
drift.

Decision:

**EXPOSE_DRIFT_ALARM_AS_A_FALSE_REVOCATION_DETECTION_COVERAGE_DELAY_FRONTIER**

Governor consequence:

Keep the cumulative exact UCB as a reference and choose a recency alarm only
through explicit external constraints:
- tolerated stable false revocation;
- required drift detection coverage;
- drift detection delay budget.

Do not hide those tradeoffs in one fixed threshold.

Claim ceiling:

**SYNTHETIC_DRIFT_ALARM_FRONTIER_FOR_ONE_REUSE_CEILING_AND_WINDOW_ONLY**
