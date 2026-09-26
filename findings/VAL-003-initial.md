# VAL-003 Initial Finding

> **Status:** CONFIRMATORY TAIL BENEFIT NOT SUPPORTED  
> **Run:** 36241864223  
> **Launch commit:** `8b16ae39aff7209ff6280e94491ee0c1fc306a64`

## Confirmatory question

Using independent new data, does CORRECT_PAGEOUT reduce the probability of a HOT-retouch stall of at least 500 ms relative to NO_HINT under the same 164 MiB transition-zone workload?

## Execution

All frozen execution checks passed:

- 40 independent GitHub-hosted runner blocks;
- 800 total trials;
- 400 CORRECT_PAGEOUT trials;
- 400 NO_HINT trials;
- arms balanced within runner blocks;
- HOT physical mapping identity balanced;
- all trial integrity checks passed;
- no OOM events.

## Pre-registered catastrophic endpoint

```text
HOT retouch latency >= 500 ms
```

Observed events:

| Arm | Events | Trials | Rate |
| --- | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 6 | 400 | 1.50% |
| NO_HINT | 7 | 400 | 1.75% |

Observed absolute difference:

```text
CORRECT - NO_HINT = -0.25 percentage points
```

## Primary confirmatory inference

The pre-registered runner-block risk-difference analysis produced:

```text
mean block risk difference = -0.0025

one-sided Monte Carlo sign-flip p
= 0.4996345

Monte Carlo standard error
≈ 0.0005000
```

The 20,000-resample cluster bootstrap interval for the absolute risk difference was:

```text
[-0.020, +0.015]
```

The pre-registered directional hypothesis is therefore **not supported**.

A two-sided diagnostic sign-flip p-value was 1.0.

## Continuous diagnostics

These are secondary and cannot rescue the negative primary result.

| Arm | Median | P90 | P95 | P99 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 0.504 ms | 79.805 ms | 135.303 ms | 655.941 ms | 1650.279 ms |
| NO_HINT | 0.777 ms | 65.972 ms | 141.800 ms | 682.214 ms | 2491.415 ms |

The continuous tail summaries do not show a clear, consistent superiority pattern.

## Design-model mismatch

The VAL-003 design Monte Carlo stressed baseline catastrophic-event rates of roughly 3–8%.

The independent validation observed a NO_HINT event rate of only 1.75%.

Therefore the realized experiment operated in a rarer-event regime than the design screen assumed.

This matters for interpretation:

- the study directly falsifies the strong exploratory expectation that the effect would resemble a 5% -> 1% reduction;
- the study does **not** establish equivalence;
- smaller absolute tail-risk reductions remain compatible with the bootstrap interval.

## Relationship to EXP-002

EXP-002 found:

- no supported central-tendency benefit for CORRECT_PAGEOUT versus NO_HINT;
- strong and reproducible harm from WRONG_PAGEOUT;
- an exploratory far-tail separation that motivated VAL-003.

VAL-003 used independent data and did **not** confirm that exploratory catastrophic-tail separation.

The combined evidence is therefore asymmetric:

```text
correct semantic PAGEOUT
    -> no established central benefit
    -> no established >=500 ms tail benefit

wrong semantic PAGEOUT
    -> large established harm
```

## Pseudo-Council conclusion

The Council converges on:

> **Do not advance CORRECT_PAGEOUT as a candidate coordination mechanism on the current evidence.**

Reasons:

1. its central-tendency benefit was not supported in EXP-002;
2. its pre-registered catastrophic-tail benefit was not supported in VAL-003;
3. its wrong/stale semantic direction has a large demonstrated downside;
4. continuing to tune the same mechanism after two independent negative benefit tests would risk research-path lock-in.

This is a mechanism-specific decision, not a claim that application semantic information has no value.

## What remains open

The evidence does not establish:

- equivalence between CORRECT_PAGEOUT and NO_HINT;
- zero value of application semantics;
- zero value of future information;
- that another intervention could not use semantic information safely;
- that the Linux baseline is globally optimal.

## Recommended next direction

Return one level upward from the PAGEOUT mechanism and ask:

> **Is there measurable decision headroom in the observed workload that any better-informed residency policy could exploit, before designing another hint mechanism?**

The next bounce should compare the strongest existing empirical/mechanistic evidence and select a bounded **Value-of-Information / decision-headroom** experiment or calculation.

Do not select another control mechanism first.

## Authority boundary

VAL-003 concerns only the declared hosted memcg workload, the declared 500 ms endpoint, and the specific CORRECT_PAGEOUT intervention.

It does not justify a generalized coordination plane or a general conclusion about Linux memory management.
