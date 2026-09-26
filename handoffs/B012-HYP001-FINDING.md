# Bounce Handoff

> **Bounce ID:** B012  
> **Status:** COMPLETE

## Objective

Read HYP-001 using only the frozen analysis and record the result.

## Evidence

Run: `36224708512`

- execution PASS;
- 20 runner blocks;
- 240 primary trials;
- 40 controls;
- exact 2^20 block sign-flip test.

Primary result:

```text
MISALIGNED / ALIGNED geometric mean latency ratio = 0.941
exact two-sided p = 0.704
cluster-bootstrap 95% ratio interval = [0.696, 1.275]
```

## Frozen finding

The pre-registered simple recency-order hypothesis is not supported.

OBS-002's residency/cost association remains, but HYP-001 did not show that final pre-burst access order can steer that cost in the predicted direction.

## Next recommended bounce

> Probe whether explicit cgroup reclaim can convert a prepared swap-backed target range into a measurably nonresident range while preserving matched control-region residency and content integrity.

This is a capability question only.

## Authority boundary

No hint, coordination, or kernel-policy experiment is authorized by HYP-001.
