# HYP-002 Initial Finding

> **Status:** RECENCY HYPOTHESIS NOT SUPPORTED / MAPPING-IDENTITY CONFOUND EXPOSED  
> **Valid run:** 36243341566  
> **Invalid predecessor:** 36243199948 (excluded)

## Question

Under 160–162 MiB memcg pressure, does randomized pre-burst access recency determine which of two matched anonymous regions retains residency, independently of which region the application will need next?

## Execution

The valid retry passed every frozen execution check:

- 16 independent GitHub-hosted runner blocks;
- 128 total factorial trials;
- all eight factor cells present in every block;
- MemoryHigh 160 / 162 MiB;
- recent identity A/B;
- future HOT identity A/B;
- no application hint or reclaim intervention;
- all trials PASS;
- content integrity preserved;
- no OOM events.

The first launch, run `36243199948`, is INVALID and excluded because of the documented integrity-baseline implementation bug.

## Primary result — recency and residency

Per runner block, the pre-registered primary contrast was:

```text
mean(recent resident fraction - older resident fraction)
```

Observed:

```text
mean contrast = -0.009035
```

Exact one-sided sign-flip over all:

```text
2^16 = 65,536
```

assignments gave:

```text
p = 0.913574
```

Runner-cluster bootstrap 95% interval:

```text
[-0.020865, +0.003025]
```

The directional recency hypothesis is **not supported**.

## Level-specific primary diagnostics

| MemoryHigh | Mean recent-older | Recent-greater rate |
| ---: | ---: | ---: |
| 160 MiB | -0.02972 | 0.484 |
| 162 MiB | +0.01165 | 0.531 |

There is no consistent positive recent-region residency advantage across the two strong-pressure levels.

## Key secondary result — semantic alignment latency

Pre-registered secondary contrast:

```text
HOT=older
versus
HOT=recent
```

Runner-block geometric mean latency ratio:

```text
misaligned / aligned = 0.9624x
```

Exact one-sided sign-flip:

```text
p = 0.571365
```

Cluster-bootstrap 95% ratio interval:

```text
[0.692, 1.256]
```

This semantic-alignment latency effect is also **not supported**.

The secondary result cannot rescue the negative primary result.

## Pre-registered mapping-identity falsification check

The recency contrast behaved very differently depending on which physical mapping was declared recent.

### recent = A

```text
mean recent-minus-older = -0.16939
positive rate           = 0.0625
```

### recent = B

```text
mean recent-minus-older = +0.15132
positive rate           = 0.953125
```

This directly weakens the recency interpretation.

The region labeled/mapped as B remained more resident regardless of which region received the final recency preparation.

## Exploratory mapping reconstruction

This analysis is post-primary but follows directly from the pre-registered falsification result.

Across all 128 trials:

```text
mean B resident fraction = 0.9323
mean A resident fraction = 0.7719
mean B - A               = +0.1604
B > A in                 = 94.5% of trials
```

By pressure level:

```text
160 MiB: mean B - A = +0.1796
162 MiB: mean B - A = +0.1411
```

The performance consequence tracked the same identity asymmetry.

Median HOT-retouch latency:

```text
160 MiB:
  HOT=A  ~256.4 ms
  HOT=B  ~0.77 ms

162 MiB:
  HOT=A  ~136.6 ms
  HOT=B  ~0.80 ms
```

These identity-specific summaries are exploratory diagnostics, not the pre-registered primary inference.

## Relationship to OBS-003

OBS-003 had a fixed A-before-B construction/touch sequence and showed strong apparent residency-selection asymmetry at 160–162 MiB.

HYP-002 deliberately reversed/randomized final recency while keeping future HOT identity independent.

The asymmetry **did not follow randomized recency**.

It stayed attached to mapping identity.

Therefore the earlier candidate explanation:

> “past recency/order drives the natural selection”

is not supported.

## Pseudo-Council conclusion

The Council converges on:

> **Do not calculate a semantic Value-of-Information from OBS-003 as if the observed A/B asymmetry were a recency-policy decision.**

A lower-level implementation/layout factor remains unresolved.

Candidate causes that now need separation include:

- mapping creation/allocation order;
- initial fault/touch order;
- virtual-address / VMA ordering;
- another stable per-mapping kernel state.

No one of these is established.

## Next research direction

Return to characterization.

Design **CHAR-002 — Mapping Identity Decomposition**.

The smallest useful factorial should independently vary:

- mapping creation order;
- initial fault/touch order;

while recording:

- virtual base addresses;
- A/B residency before reuse;
- pressure counters.

Final recency should be held neutral or explicitly controlled rather than used as the primary factor.

Only after the stable A/B asymmetry is explained or neutralized should the lab resume a formal semantic Value-of-Information calculation.

## Authority boundary

HYP-002 does not show that Linux ignores all recency information.

It shows that the specific randomized final-recency manipulation did not explain residency selection in this bounded workload, while a strong mapping-identity asymmetry remained.
