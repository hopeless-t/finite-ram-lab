# EXP-003 Initial Finding

> **Status:** NET BENEFIT SUPPORTED IN MISALIGNED STRATUM / WRONG-ACTION RISK REMAINS CONTEXT-DEPENDENT
> **Run:** 36253713012
> **Aggregate artifact:** 10910048127

## Frozen question

At the independently justified high-headroom 160–162 MiB conditions, can the existing 16 MiB `MADV_PAGEOUT` semantic preparation capture part of the HYP-003 information-gap headroom?

The primary benefit comparison was pre-registered in the naturally misaligned stratum:

```text
CORRECT_PAGEOUT
vs
NO_HINT
```

## Execution

EXP-003 passed all frozen execution checks:

- 16 independent runner blocks;
- 384 total trials;
- all trial jobs PASS;
- aggregate PASS;
- no advice in NO_HINT;
- advice succeeded when required;
- page-aligned addresses and integrity checks PASS.

## Primary mechanism-sensitive endpoint

Misaligned HOT-retouch latency:

```text
CORRECT_PAGEOUT / NO_HINT geometric mean ratio
= 0.01446
```

Exact one-sided sign-flip:

```text
p = 1.5259e-05
```

Runner-cluster bootstrap 95%:

```text
[0.00459, 0.04988]
```

Thus CORRECT_PAGEOUT strongly reduced future HOT-retouch cost in the frozen misaligned stratum.

Equivalently, the reciprocal ratio is about 69×, but the project reports the pre-registered CORRECT/NO_HINT ratio to avoid turning that reciprocal into a generalized speedup claim.

## End-to-end interval

Misaligned total work interval:

```text
CORRECT_PAGEOUT / NO_HINT geometric mean ratio
= 0.17723
```

Exact one-sided sign-flip:

```text
p = 1.5259e-05
```

Bootstrap 95%:

```text
[0.11443, 0.28538]
```

The mechanism-sensitive improvement therefore did not disappear when PAGEOUT call cost and burst work were included.

Under the frozen EXP-003 classification, this supports **net benefit in the misaligned stratum**.

## Aligned control

When historical residency and future HOT demand were already aligned, CORRECT_PAGEOUT did not show a supported benefit over NO_HINT.

HOT-retouch ratio:

```text
1.48388
p(less) = 0.81580
bootstrap 95% = [0.75851, 3.42353]
```

Total-work ratio:

```text
0.91722
p(less) = 0.19316
bootstrap 95% = [0.77363, 1.11448]
```

Therefore the strong benefit is not promoted as a universal PAGEOUT effect.

It is conditional on the information-gap / misalignment regime identified before EXP-003.

## Wrong/stale Red-Team

### Aligned stratum

WRONG_PAGEOUT was strongly harmful relative to NO_HINT.

HOT-retouch:

```text
WRONG / NO_HINT = 39.35×
p(greater) = 1.5259e-05
bootstrap 95% = [14.72×, 92.19×]
```

Total work:

```text
WRONG / NO_HINT = 2.439×
p(greater) = 0.000198
bootstrap 95% = [1.770×, 3.305×]
```

### Misaligned stratum

WRONG_PAGEOUT was much worse than the correct semantic action:

```text
HOT WRONG / CORRECT = 41.97×
bootstrap 95% = [15.77×, 106.68×]

TOTAL WRONG / CORRECT = 3.292×
bootstrap 95% = [2.399×, 4.403×]
```

However, WRONG_PAGEOUT was not worse than NO_HINT in this already-misaligned stratum:

```text
HOT WRONG / NO_HINT = 0.607×
TOTAL WRONG / NO_HINT = 0.583×
```

The pre-registered greater-than-NO_HINT tests therefore do not support harm in that particular stratum.

This asymmetry is scientifically important.

It means "wrong semantic action" is not a single context-free cost. Its danger depends on whether the baseline residency state was already good or already mismatched.

## Interpretation

EXP-003 changes the project state materially.

The chain is now:

```text
past fault/touch cue
        ↓
residency selection
        ↓
future semantic need can disagree
        ↓
misalignment has large cost
        ↓
correct cold-region PAGEOUT can steer reclaim
        ↓
HOT reuse and total work improve
```

This is the first intervention in Finite RAM Lab that captures a substantial fraction of previously measured information headroom under a prospectively justified pressure regime.

But the same primitive can strongly damage an already-correct residency state when directed at future HOT data.

Therefore the main research question changes from:

> Does semantic information have usable value?

to:

> **What confidence / gating condition is sufficient to apply a semantic residency action only when expected benefit exceeds intervention risk?**

## What is not established

EXP-003 does not establish:

- production workload prevalence of the misaligned state;
- a deployable application API;
- safe signal freshness requirements;
- optimal PAGEOUT range;
- general Linux-wide benefit;
- that PAGEOUT is the final mechanism;
- that an always-on semantic controller is safe.

The 16 MiB range was frozen as a mechanism probe and must not be tuned post hoc from EXP-003.

## Next research direction

The next experiment should test **selective gating**, not a more aggressive hint.

A gate should decide between:

```text
ACT: apply the already-tested correct semantic preparation
NO-ACT: leave the OS alone
```

using only information that would actually be available before the intervention.

The key scientific target is the decision boundary:

```text
expected benefit of acting
>
expected cost of false activation
```

A future gate experiment must include stale/wrong-signal injection and preserve NO_HINT as fallback.

## Authority boundary

EXP-003 supports a bounded net benefit of the existing semantic PAGEOUT probe when the future-needed region conflicts with the historical fault-order cue.

It does not authorize deployment, always-on hints, or an architecture commitment.
