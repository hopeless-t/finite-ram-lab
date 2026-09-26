# CHAR-002 Initial Finding

> **Status:** INITIAL FAULT/TOUCH-ORDER EFFECT SUPPORTED / CREATION-ORDER EFFECT NOT SUPPORTED / ADDRESS EFFECT UNRESOLVED  
> **Run:** 36246723145  
> **Artifact:** CHAR-002-aggregate-36246723145 / 10907138130

## Question

What lower-level factor explains the stable A/B residency asymmetry that survived HYP-002 final-recency randomization under 160–162 MiB memcg pressure?

CHAR-002 decomposed:

- separate-mapping creation order;
- initial fault/touch order;
- virtual-address position.

CHAR-002 is characterization, not a semantic-demand or control experiment.

## Execution

All frozen execution checks passed:

- 16 independent runner blocks;
- 192 total trials;
- complete factorial cells;
- all trials PASS;
- no OOM;
- content integrity preserved;
- all measured addresses page aligned.

## Frozen mechanism contrasts

### S1 — Separate-VMA creation order

~~~text
resident(second-created) - resident(first-created)
= +0.006714

exact two-sided sign-flip p = 0.573639
cluster-bootstrap 95% = [-0.014912, +0.025932]
~~~

The experiment does **not** support a stable creation-order residency effect.

### S2 — Separate-VMA initial fault/touch order

~~~text
resident(second-faulted) - resident(first-faulted)
= +0.081242

exact two-sided sign-flip p = 6.1035e-05
cluster-bootstrap 95% = [+0.045693, +0.131753]
~~~

The region faulted/touched second retained substantially more residency after the burst.

### H1 — Shared-VMA virtual-address position

~~~text
resident(upper half) - resident(lower half)
= +0.023714

exact two-sided sign-flip p = 0.110657
cluster-bootstrap 95% = [+0.000126, +0.051634]
~~~

The two uncertainty summaries do not give a clean common conclusion.

The block-randomization result does not strongly support a stable address-position effect, while the bootstrap interval is weakly positive.

Therefore address position remains **UNRESOLVED**, not promoted to a mechanism finding.

### H2 — Shared-VMA initial fault/touch order

~~~text
resident(second-faulted) - resident(first-faulted)
= +0.099680

exact two-sided sign-flip p = 3.0518e-05
cluster-bootstrap 95% = [+0.062176, +0.142443]
~~~

The same second-faulted residency advantage reproduced when both regions were halves of one shared VMA.

## Pressure-level consistency

At 160 MiB:

~~~text
Separate-VMA fault effect = +0.08904
Shared-VMA fault effect   = +0.11243
~~~

At 162 MiB:

~~~text
Separate-VMA fault effect = +0.07344
Shared-VMA fault effect   = +0.08693
~~~

The fault/touch-order effect was positive in both layout families and both pressure levels.

## Creation/address confounding report

For the separate-VMA family:

~~~text
second-created-is-higher-address rate = 0.0
second-created-is-lower-address rate  = 1.0
~~~

Creation order and numeric address order were therefore perfectly collinear in the hosted environment.

This is why the separate-VMA family alone cannot separate those mechanisms.

However, the shared-VMA family removes separate mapping creation order and still shows the strong fault/touch-order effect.

## Interpretation

The strongest supported explanation for the prior stable A/B asymmetry is now:

> **which logical region is initially faulted/touched second materially changes which region remains resident after later memory pressure.**

This is stronger than an observational correlation because CHAR-002 actively counterbalanced the initial fault/touch order.

The result also reconciles the earlier studies:

~~~text
OBS-003 / HYP-002:
A was initially faulted before B
        ↓
B tended to remain more resident

HYP-002:
later/final recency was randomized
        ↓
B asymmetry persisted

CHAR-002:
initial fault order itself was randomized
        ↓
the residency advantage followed the region faulted second
~~~

Thus HYP-002's failure was informative: a later recency manipulation did not erase the state established around initial fault/touch ordering.

## What is not yet established

CHAR-002 does not establish:

- the exact kernel data structure or reclaim heuristic responsible;
- that numeric virtual address is irrelevant;
- that all Linux workloads have the same effect;
- that the effect is a kernel defect;
- that future application semantics improve decisions;
- that a memory coordinator is warranted.

In particular, “initial fault/touch order” still combines several low-level phenomena:

- temporal order of page faults;
- page insertion/aging state;
- the time gap between the two region populations;
- potentially another page-level state correlated with that order.

## Council conclusion

The mapping-identity confound is no longer mysterious enough to justify treating A/B identity as an unexplained fixed property.

The next useful test is a same-experiment information-gap study that independently randomizes:

~~~text
initial fault/touch order
and
future semantic HOT identity
~~~

under 160–162 MiB pressure.

That study should ask whether residency follows the past fault-order cue while future demand is independently assigned.

Formal Value-of-Information calculation should remain paused until that direct mismatch is measured.

## Authority boundary

CHAR-002 supports a bounded causal effect of initial fault/touch ordering on later residency in this hosted memcg workload.

It does not yet establish the value of application semantic information or authorize a coordination mechanism.
