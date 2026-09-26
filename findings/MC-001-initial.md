# MC-001 Initial Finding

> **Status:** INITIAL SYNTHETIC FINDING / DECISION SUPPORT  
> **Run:** 36213541839  
> **Source commit:** `1cf5875b0c2e96daa29d5efdcbc567086730849e`

## Experiment

MC-001 ran 16,000 seeded synthetic trials across four access-pattern families.

The metric is:

```text
fault_rate_gap = LRU fault rate - OPT fault rate
```

OPT is Belady's perfect-future oracle for the same synthetic trace and capacity.

## Aggregate result

| Family | Trials | Mean gap | P90 gap | P99 gap | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| bursty | 4000 | 0.1112 | 0.1298 | 0.1386 | 0.1532 |
| sequential_scan | 4000 | 0.1606 | 0.2743 | 0.3097 | 0.3255 |
| shifting_hotset | 4000 | 0.0585 | 0.0849 | 0.1023 | 0.1209 |
| stable_hotset | 4000 | 0.0804 | 0.1099 | 0.1278 | 0.1537 |

## Finding

Under the declared synthetic generator, every tested family contained a positive replacement-information gap.

The largest gap among these four families occurred in the `sequential_scan` family.

This means only that perfect future information has substantial theoretical value for some generated traces.

## Non-claims

This does **not** establish:

- that Linux behaves like the LRU simulator;
- that Linux has a defect;
- that application hints can recover the OPT bound;
- that a userspace coordinator improves real performance.

## Research impact

A scan-disturbance workload should be prioritized as an early controlled OBS/CHAR workload after the hosted runner's memory-limit control surface is validated.

MC-001 therefore narrows the next physical/hosted experiment search space without replacing it.
