# OBS-003 Initial Finding

> **Status:** NATURAL MISALIGNMENT MAP COMPLETE / DECISION-HEADROOM SIGNAL PRESENT  
> **Run:** 36242552339

## Question

Across the 160–168 MiB transition region, how often does the unmodified NO_HINT workload reach HOT reuse with the future-needed HOT semantic region not fully resident?

## Execution

All frozen execution checks passed:

- 32 independent GitHub-hosted runner blocks;
- 5 MemoryHigh levels;
- 2 trials per level per block;
- 320 total NO_HINT trials;
- HOT physical mapping identity balanced A/B at every level in every block;
- all trials passed;
- content integrity preserved;
- no OOM events.

## Primary misalignment map

Primary definition:

```text
misaligned = HOT resident fraction < 1.0
```

immediately before HOT reuse.

| MemoryHigh | Misaligned | Trials | Rate | Cluster-bootstrap 95% |
| ---: | ---: | ---: | ---: | ---: |
| 160 MiB | 38 | 64 | 0.5938 | [0.5313, 0.6719] |
| 162 MiB | 37 | 64 | 0.5781 | [0.5156, 0.6406] |
| 164 MiB | 7 | 64 | 0.1094 | [0.0313, 0.2031] |
| 166 MiB | 4 | 64 | 0.0625 | [0.0000, 0.1563] |
| 168 MiB | 1 | 64 | 0.0156 | [0.0000, 0.0469] |

The natural opportunity rate is therefore strongly pressure-dependent.

The largest sampled change occurs between 162 and 164 MiB.

## Conditional latency diagnostic

This comparison is descriptive, not a randomized intervention.

| MemoryHigh | Median HOT reuse if misaligned | Median HOT reuse if fully resident |
| ---: | ---: | ---: |
| 160 MiB | 233.514 ms | 0.789 ms |
| 162 MiB | 130.067 ms | 0.763 ms |
| 164 MiB | 53.332 ms | 0.775 ms |
| 166 MiB | 62.118 ms | 0.754 ms |
| 168 MiB | 21.029 ms | 0.514 ms |

All three >=500 ms events observed in OBS-003 occurred in misaligned trials.

This is consistent with OBS-002 and EXP-001, but the conditional comparison in OBS-003 alone is not causal.

## Decision-headroom interpretation

OBS-003 closes an important gap left by EXP-002 / VAL-003.

The tested CORRECT_PAGEOUT mechanism failed to establish benefit, but the baseline does not have zero selection opportunity.

At 160–162 MiB, the future-needed HOT region was naturally not fully resident in roughly 58–59% of trials.

At 164 MiB the opportunity rate fell to about 11%, and by 168 MiB it was near zero.

Therefore:

> **Residency-selection headroom exists, but it is concentrated in the stronger-pressure region rather than uniformly across the transition zone.**

This helps explain why a mechanism tested only at 164 MiB can have little aggregate room to improve despite the very large causal cost of the wrong residency identity shown by EXP-001.

## Exploratory A/B ordering observation

This was not the pre-registered OBS-003 primary analysis.

The underlying NO_HINT workload touches mapping A before mapping B during initial setup.

At 160 and 162 MiB, residency outcomes were strongly tied to that physical/order identity.

### 160 MiB

For HOT=A trials:

```text
HOT misaligned: 32 / 32
```

For HOT=B trials:

```text
HOT misaligned: 6 / 32
```

### 162 MiB

For HOT=A trials:

```text
HOT misaligned: 32 / 32
```

For HOT=B trials:

```text
HOT misaligned: 5 / 32
```

Among trials where exactly one semantic region lost full residency, the missing region was overwhelmingly mapping A.

This suggests a strong candidate explanation:

> under heavier pressure, past access/allocation ordering may dominate natural residency selection, while future semantic demand is balanced independently of that ordering.

This is **hypothesis-generating**, not a frozen causal finding, because OBS-003 did not randomize/reverse the pre-burst A/B access order.

## Relationship to prior evidence

The evidence chain is now:

```text
EXP-001
residency identity causally matters
        ↓
EXP-002 / VAL-003
tested semantic PAGEOUT does not establish benefit
        ↓
OBS-003
natural residency-selection opportunity is frequent
at 160–162 MiB, but much rarer at 164+ MiB
        ↓
exploratory signal:
selection may be driven by past recency/order rather than future semantics
```

## Pseudo-Council conclusion

A formal Value-of-Information / decision-headroom program is now warranted.

However, do **not** immediately compute a grand scalar “value” by combining mismatched studies.

First confirm the apparent information mismatch directly:

> Does randomized pre-burst recency/order determine which matched region loses residency under 160–162 MiB pressure, independently of which region will be needed next?

This would establish whether the OS-visible past-use cue and application-known future-use cue are genuinely separable in the same experiment.

## Next research direction

Design a balanced factorial HYP-002 study with:

- semantic HOT identity A/B;
- recent/last-touched identity A/B;
- MemoryHigh 160 and 162 MiB;
- equal region sizes and equal touch counts;
- direct mincore residency observation before reuse.

No new memory-management mechanism should be introduced.

## Authority boundary

OBS-003 measures natural memcg-pressure residency outcomes in the declared workload.

It does not prove that Linux makes an error, that recency is globally wrong, or that an application hint would improve performance.
