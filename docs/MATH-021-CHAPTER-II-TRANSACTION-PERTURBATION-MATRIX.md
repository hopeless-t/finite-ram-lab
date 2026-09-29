# MATH-021 — Chapter II Transaction Perturbation Matrix

> Status: FROZEN DESIGN / NOT AUTHORIZED / NO PHYSICAL RUN  
> Prerequisite: B404 native observer + epoch wiring passes  
> Goal: causally distinguish state-preserving contamination from state-destroying transitions.

## 1. Chapter II hypothesis

The leading hypothesis is no longer:

> failures are random misses of a Q64 state.

It is:

> once a Q64 reset is directly verified, the stock arithmetic is deterministic until a discrete state-changing event occurs.

Formally, for a verified epoch (E),

[
P(	ext{canonical target pattern} mid E, 
eg I)
]

should remain high, while the main uncertainty moves to the event process (I):

[
I in {
	ext{unexpected refill},
	ext{drain},
	ext{PTE growth},
	ext{CPU mismatch},
	ext{worker error},
	ext{trace gap}
}.
]

A positively classified LRU release is explicitly not in this invalidator set.

## 2. Why this is the best current target

Three earlier results narrow the search space.

### PTE path

Controlled-spawn v2 preconditioned the target PTE table and observed:

- 0 measured VmPTE-growth events across the measured sequence.

So PTE growth can be engineered away in the clean lane.

### Release path

The historical negative bait events retained the predicted terminal stock phase.

OBS-005/MATH-016 then directly grounded the recurrent -17 lane as a shared per-CPU LRU release.

Therefore release-only is a strong candidate for:

[
	ext{observable contamination} 
eq 	ext{stock-state mutation}.
]

### Remaining state-loss path

OBS-006 rejected two trials because unexpected refill occurred after state establishment.

Thus the highest-value remaining distinction is:

[
	ext{release-only}
quad	ext{vs}quad
	ext{true stock mutation}.
]

## 3. The perturbation matrix

Use four orthogonal arms, four identities each.

### CLEAN

No intentional perturbation.

Prediction:

[
VERIFIED 	o EXECUTE 	o TARGET_MATCH 	o COMMIT.
]

### RELEASE_ONLY

After direct Q64 verification, deliberately construct one source-grounded shared-LRU release during execution.

Prediction:

- release receipt increments;
- expected residual does not change because of the release;
- the b63 terminal phase remains canonical;
- no INVALIDATE solely because memory.current fell.

This is the positive control for the new observer.

### UNEXPECTED_REFILL

After direct Q64 verification, intentionally take one extra stock-consuming transition such that a direct Q64/refill appears before the frozen TARGET boundary.

Prediction:

[
UNEXPECTED_REFILL 	o INVALIDATED.
]

It must not become TARGET_FAIL.

It must not become a new primer in the same epoch.

### PTE_GROWTH

After direct Q64 verification, deliberately fault a page in an untouched PTE-table region during the measured phase.

Prediction:

[
VmPTE growth 	o INVALIDATED
]

even if net memory.current looks Q64-like or the later terminal pattern would otherwise match.

This is the negative control for the guard-precedence rule.

## 4. Why these four arms are stronger than passive sampling

A passive pilot can show that the protocol works when nothing unusual happens.

It cannot demonstrate that the classifier is causal.

The perturbation matrix asks the classifier to distinguish:

[
	ext{harmless release}
]

from:

[
	ext{state mutation}
]

under deliberately constructed conditions.

If the classifier treats all three perturbations the same, it is too coarse.

If it ignores all three, it is unsafe.

The required result is asymmetric:

- RELEASE_ONLY: preserve state;
- UNEXPECTED_REFILL: invalidate;
- PTE_GROWTH: invalidate.

## 5. New telemetry requirement: state age

Every packet should add two derived coordinates:

[
a_t = 	ext{touches since VERIFIED}
]

and:

[
	au_t = 	ext{elapsed ns since VERIFIED}.
]

Also record:

- expected residual before touch;
- expected residual after touch;
- invalidator type.

This turns every invalidation into a point on an epoch-hazard map.

The first pilot will not estimate a smooth hazard function reliably, but it will tell us whether invalidations cluster by:

- touch age;
- wall-clock age;
- event type;
- phase.

## 6. Working hazard hypothesis

Do not assume a memoryless Bernoulli failure process.

The current evidence points toward discrete finite-structure transitions:

- memcg charge batch: 64 pages;
- per-CPU/shared stock operations;
- PTE allocation boundaries;
- shared per-CPU LRU batching.

The current Linux source still defines MEMCG_CHARGE_BATCH as 64 pages, and LRU movement is staged through per-CPU folio batches. This makes an event-driven hazard model more plausible than a single constant per-touch failure probability.

Working model:

[
h(t) = sum_j h_j(t)
]

where each (h_j) corresponds to a distinct transition mechanism rather than one homogeneous random error process.

This remains a hypothesis until the native transactional trace measures it.

## 7. Key falsifiers

The Chapter II working theory is weakened if any of these occur with complete receipts:

1. RELEASE_ONLY changes residual phase.
2. CLEAN produces a valid uninterrupted TARGET_FAIL.
3. UNEXPECTED_REFILL still reaches COMMIT in the same epoch.
4. PTE_GROWTH still reaches COMMIT in the contaminated epoch.
5. hard re-prime succeeds using an old epoch receipt.
6. canonical phase changes with no observer-visible invalidator.

Case 6 would be especially important: it would imply the B400 observer is still missing a state-changing mechanism.

## 8. Order of execution

Do not launch this matrix before B404.

Sequence:

1. B404: prove native packet wiring and epoch machinery.
2. TX-PERTURBATION-MATRIX-v1: causally validate classifier boundaries.
3. Only then design a larger natural epoch-hazard panel.
4. Reliability certification remains later.

## 9. Claim ceiling

Even if all 16 perturbation trials behave exactly as predicted, claim only:

> the classifier responded correctly to these deliberately constructed mechanism challenges.

Do not convert the result into a population-level reliability percentage.

## 10. Second-chapter research direction

Chapter I asked:

> where is the rare state, and can we construct it?

Chapter II asks:

> once the state is verified, what events preserve it, what events destroy it, and can the protocol prove the difference before commit?

That is now the main experimental object.
