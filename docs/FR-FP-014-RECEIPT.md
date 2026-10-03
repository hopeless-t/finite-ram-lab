# FR-FP-014 Receipt

Status: **PASS / HOSTED WARM-COLD RESTORE PILOT QUALIFIED**

Parent: **FR-FP-013**

- workflow run: 37145363545
- job: 111268063314
- execution head: 306941a61cef7f56c03ea7d490ac7551a5465052
- paired blocks: 8
- state size: 8 MiB

Physical tier separation before restore:

WARM_PAGECACHE:
- median pre-restore file resident fraction: 1.0

COLD_DONTNEED:
- median pre-restore file resident fraction: 0.0

After restore:
- both arms median file resident fraction: 1.0
- every restore read exactly 8 MiB
- every restored state passed sentinel integrity
- every restore materialized 8 MiB process RSS/RssAnon

Restore read latency:

WARM_PAGECACHE:
- median read: 847,494 ns = 0.847 ms
- median total restore: 860,328 ns = 0.860 ms

COLD_DONTNEED:
- median read: 3,102,932.5 ns = 3.103 ms
- median total restore: 3,117,775 ns = 3.118 ms

Paired cold/warm read ratios:
- 3.610
- 3.511
- 3.733
- 3.521
- 3.767
- 3.898
- 3.657
- 6.589

Median paired ratio:
- 3.695x

Median read-time penalty:
- about 2.255 ms per 8 MiB state

Interpretation:

The WARM and COLD tiers are physically distinct and both restore exactly.

In this hosted pilot, evicting the 8 MiB file from page cache materially reduced
residency but increased median restore-read latency by roughly 3.7x.

The latency ordering was measured after the gate was frozen; it was not assumed
as a PASS condition.

Decision:

**MEASURE_RESTORE_COST_SEPARATELY_FROM_RESIDENCY_BENEFIT_BEFORE_TIER_POLICY_SELECTION**

Next:

Derive a break-even tier frontier as a function of state reuse probability and
an explicit memory shadow price, rather than inventing a hidden common utility
weight.

Claim ceiling:

**HOSTED_LINUX_WARM_COLD_RESTORE_PILOT_ONLY**
