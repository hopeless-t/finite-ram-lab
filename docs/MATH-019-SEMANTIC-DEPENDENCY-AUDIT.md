# MATH-019 — Semantic Dependency Audit after Transactional Reclassification

> **Status:** COMPLETE / RETROSPECTIVE DEPENDENCY AUDIT  
> **Inputs:** MATH-001..018, MEMCG-001..005G, OBS-005/006, B400/B401  
> **No new physical run.**

## 1. Research question

Does the B400/B401 redefinition of SUCCESS/FAIL force finite-ram-lab to discard its old samples and recalculate the mathematical program from zero?

Short answer:

**No.**

The semantic correction is large, but the numerical damage is much smaller than it first appears.

The key reason is that many of the earlier mathematical models were fitted to an observable event:

[
Z_i = 1[Delta_i^{first}=0]
]

rather than to an independently verified target-mechanism failure.

B400 changes what that event *means*. It does not change whether it happened.

Therefore much of the natural-state mathematics survives numerically and must be **reinterpreted**, not rerun.

## 2. Three layers that must no longer be conflated

### Layer O — raw observation

Examples:

- first-touch delta 0
- first-touch net +64
- later Q64 touch index
- VmPTE +4 KiB
- CPU mismatch
- negative memory.current emission
- direct charge/refill trace

Historical observations are immutable.

### Layer S — hidden-state interpretation

Examples:

- favorable initial phase
- residual stock near exhaustion
- normalization depth
- PTE-mediated perturbation
- release-only contamination

This layer can improve as evidence improves.

### Layer C — certification outcome

Examples:

- VERIFIED
- INVALIDATED
- TARGET_FAIL
- SUCCESS

This is the layer B400 changes most strongly.

The old error was allowing an O-layer observation such as net +64 or net 0 to stand in for a C-layer conclusion.

## 3. Mathematical invariance test

Suppose a historical natural-state model was:

[
P(Z_i=1 mid X_i;	heta)
]

where:

[
Z_i=1
]

means the first measured touch had exact-zero net delta.

If B400 changes the verbal interpretation from:

> mechanism failure

to:

> first touch did not land on a verified reset boundary / hidden-state phenotype

then neither (Z_i) nor (X_i) changes.

Therefore:

[
mathcal L(	heta;Z,X)
]

is unchanged.

The fitted coefficients, Fisher tests, block bootstrap, threshold localization, and Monte Carlo based directly on (Z) do **not** need to be recomputed merely because the semantic label changed.

What changes is the estimand name and the causal claim ceiling.

This is the central result of B402.

## 4. Where the old mathematics really breaks

The old and new success variables are not equivalent.

Historical coarse success:

[
Y_{old}=1[	ext{net observation matched frozen pattern}]
]

B400 accepted success:

[
Y_{tx}=1[
Q64_{direct}
land refill63
land PTE_{clean}
land CPU_{match}
land trace_{complete}
land uninterrupted epoch
land target match
land commit
]
]

For historical controlled-spawn, several inputs to (Y_{tx}) were never recorded.

Therefore:

[
Y_{tx}
]

is **missing / non-identifiable** in that dataset.

It is mathematically wrong to estimate B400 correctness by either:

[
49/72
]

or:

[
55/55.
]

It is equally wrong to interpret the fail-closed historical replay's zero certified accepts as:

[
P(Y_{tx}=1)=0.
]

The correct statement is:

> the historical run cannot identify the new accepted-result correctness estimand.

This distinction is stronger than a simple refit requirement. It is a missing-variable problem requiring a successor experiment.

## 5. MATH-001..018 audit

| Model | Disposition | Numerical recompute? | New interpretation |
|---|---|---:|---|
| MATH-001 | **KEEP** | No | Q64 resettable staircase + hidden phase survives |
| MATH-002 | **KEEP** | No | secondary geometric lens only |
| MATH-003 | **REINTERPRET** | No | failure-depth -> normalization/initial-state depth phenotype |
| MATH-004 | **REINTERPRET** | No | capture rate -> natural exact-zero incidence |
| MATH-005 | **REINTERPRET** | No | threshold -> initial-state capture propensity |
| MATH-006 | **REINTERPRET** | No | Monte Carlo locates rare-state capture region, not mechanism-failure region |
| MATH-007 | **REINTERPRET** | No | exact-zero morphology analysis survives; failure terminology narrows |
| MATH-008 | **KEEP** | No | argv-width identifiability audit unaffected |
| MATH-009 | **KEEP** | No | source-grounded PTE/fault-path mechanism unaffected |
| MATH-010 | **KEEP** | No | historical alias-breaker design calibration |
| MATH-011 | **REINTERPRET** | No | natural-state discriminator survives; PTE growth also becomes INVALIDATE transactionally |
| MATH-012 | **REINTERPRET** | No | capacity/PTE decomposition survives under hidden-state semantics |
| MATH-013 | **SUPERSEDED** | No | stock arithmetic survives; old success token replaced by B400 receipts |
| MATH-014 | **REINTERPRET** | No | natural models survive; 55/55 remains conditional pattern matching only |
| MATH-015 | **SUPERSEDED** | No | descriptive -17 statistics survive; H17-STOCK origin replaced by shared-LRU evidence |
| MATH-016 | **KEEP** | No | direct shared-LRU handoff mechanism is part of new observer |
| MATH-017 | **KEEP** | No | semantic reframe itself |
| MATH-018 | **KEEP** | No | new transactional reliability mathematics |

### Key surprise

There is currently **no MATH document that requires a mandatory numerical refit solely because B400 changed the label semantics**.

That does not mean nothing changes.

It means the main repair is:

- rename estimands;
- lower causal claim ceilings;
- separate natural-state and transactional populations;
- supersede two outdated mechanism/design claims;
- collect new data for the genuinely new estimand.

## 6. MATH-015 is the strongest true theory replacement

MATH-015 proposed a specific H17-STOCK/drain origin for the recurrent -17 signature.

Its descriptive findings remain useful:

- discrete +17 pre-current modes;
- strong association with later -17;
- subtract-17 return toward clean support;
- phase-independent event timing.

But OBS-005 and MATH-016 subsequently constructed a shared per-CPU LRU-batch handoff that directly produced:

[
page_counter_uncharge(...,17)
]

for folios owned by another task/cgroup.

Therefore the old H17-STOCK origin hypothesis is superseded.

This is a genuine example where later instrumentation changed a mechanism hypothesis rather than merely relabeling an endpoint.

## 7. MEMCG experiment audit

### Reusable without rerun

MEMCG-001/002/003/003B/004/005/005B remain valid for the questions they actually measured.

Their strongest lessons survive:

- Q64 quantization;
- CPU-conditioned hidden phase;
- destructive observation;
- passive accounting not directly revealing stock eviction;
- calibrated reset arithmetic;
- non-compositional normalization;
- migration/control-path interference.

### Reusable with semantic relabeling

MEMCG-005C/D/E/F and G-A/B/D/E/F/G0 remain valuable datasets.

Their first-touch Q64/zero outcomes now estimate combinations of:

- initial hidden phase;
- reset-boundary placement;
- natural normalization burden;
- capacity-conditioned phenotype incidence.

They do not estimate target mechanism correctness.

### Needs a successor, not a literal repeat

Controlled-spawn v2 is the only central experiment that must be followed by a new native-receipt experiment before the new correctness question can be answered.

Do **not** rerun the old experiment unchanged.

The successor must emit B400 receipts from the beginning.

## 8. What happens to the CAP10-neighborhood result?

It survives.

G-F and G0 modeled:

[
P(first touch exact-zero mid capacity, block, admission,ldots)
]

The exact-zero rows do not change under B400.

Therefore the observed CAP10-neighborhood association remains a real association in the natural-state population.

What changes is the statement:

Old unsafe wording:

> CAP10 changes failure probability.

New wording:

> CAP10-neighborhood conditions are associated with the probability of entering/carrying the measured exact-zero initial-state phenotype under the LOW admission process.

This is a weaker causal claim but a more accurate scientific object.

## 9. What happens to the 98.374% result?

The number survives exactly.

[
121/123=98.374%
]

But its estimand becomes:

[
P(	ext{first measured touch presents Q64-like reset-boundary observation}
mid REMOTE_LOW)
]

rather than:

[
P(	ext{target mechanism succeeds}mid REMOTE_LOW).
]

REMOTE_LOW therefore remains useful as a **normalization-cost predictor**.

It can still reduce expected work even though it is no longer a correctness boundary.

## 10. What happens to 55/55?

It also survives, but narrowly.

[
55/55
]

still means:

> among historically observed Q64-primer-qualified trials, the frozen b62/b63/b64 terminal phase pattern matched in all 55.

It does **not** mean:

> B400 accepted-result correctness is 100%.

The direct B400 receipt chain was not collected in that run.

Thus:

[
P(	ext{terminal pattern match}mid historical primer)
]

is measured,

while:

[
P(	ext{correct}mid protocol emits SUCCESS)
]

is not.

## 11. Sampling consequence

The old natural-state samples should **not** be discarded.

They are now more cleanly understood as a hidden-state ecology dataset.

New sample acquisition is required only for quantities that did not exist observationally before B400:

1. B400 accepted-result correctness;
2. genuine TARGET_FAIL rate;
3. invalidation rate by cause;
4. re-prime count distribution;
5. attempts-to-valid-terminal distribution;
6. abort/abstention rate;
7. normalization depth under direct receipts.

This substantially reduces the amount of experimental work compared with restarting the entire lab.

## 12. Pseudo-Council

### Statistician

If the binary response row did not change, do not refit simply because its name changed.

Refit only when the target variable or population changes.

### Causal modeler

Capacity coefficients from natural panels must not be transported into target correctness without a bridge experiment.

### Measurement specialist

Historical net-delta data cannot reconstruct missing direct charge/refill receipts.

Treat this as non-identifiability, not zero success.

### Kernel/mechanism reviewer

Q64, PTE, and LRU mechanism evidence is strengthened, not weakened, by the observer work.

### Falsification reviewer

Preserve frozen endpoints and explicitly mark MATH-015's old origin hypothesis as superseded.

### Council convergence

**5/5 converge.**

The lab does not restart.

It forks the research object into two linked programs:

[
	ext{Natural Hidden-State Ecology}
]

and:

[
	ext{Transactional Correctness}
]

with Q64/reset-state mechanics forming the bridge.

## 13. New research topology

### Track N — Natural Hidden-State Ecology

Reuse G-A/G-B/G-D/G-E/G-F/G0.

Questions:

- what controls initial residual phase?
- why does the CAP10-neighborhood association exist?
- what determines depth1 vs deep tail?
- how do PTE and other perturbations reshape the phenotype distribution?

### Track T — Transactional Correctness

Use B400-native receipts.

Questions:

- can a verified reset be acquired reliably?
- how often is it invalidated?
- how costly is re-prime?
- after a verified uninterrupted epoch, does the target ever genuinely mismatch?
- how high is accepted-result correctness?

### Bridge

[
X
ightarrow
P(	ext{normalization burden})
ightarrow
verified reset
ightarrow
target transition
]

This replaces the old single-step idea:

[
Xightarrow SUCCESS/FAIL.
]

## 14. Immediate decision

Do not recollect the natural-state corpus.

Do not globally rerun MATH-001..018.

Do not use historical controlled-spawn to estimate B400 correctness.

Next engineering/research bounce:

**build the native controlled-spawn -> B400 receipt bridge and design the smallest information-maximizing transactional pilot.**

The large reliability run remains deferred.
