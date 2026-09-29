# COUNCIL-2026-09-30 — Transfer external memory-systems findings into finite-ram-lab

> **Status:** CONVERGED
> **Physical execution:** NONE
> **Inputs:** canonical 4,680-trial census, MATH-014, controlled-spawn v2, Strata intake, Sep-30 external reconnaissance, updated Linux page_counter-stock v6 and tiered-memcg RFC.

## Council roles

The pseudo-Council used seven adversarial roles:

1. statistical modeling;
2. Linux MM / memcg;
3. measurement and instrumentation;
4. finite-memory systems architecture;
5. AI runtime / tiering;
6. falsification / red-team;
7. maintainer / scope control.

The purpose was not to vote on truth. It was to force incompatible assumptions into the open and converge on a
transfer plan that preserves existing evidence.

# Atomic evidence ledger

## Internal evidence atoms

### I-01 — Natural incidence baseline

Across G-F/G0 valid LOW trials, the CAP10+ step is the best block-held-out predictor among the fitted model ladder.

Transfer:
keep it as the predictive baseline and regression yardstick.

Do not transfer:
a causal claim that capacity 10 itself is the mechanism.

### I-02 — Richer natural-incidence models did not earn promotion

Interaction, hierarchical, and two-regime mixture models did not beat the simple step on block-held-out log loss.

Transfer:
require held-out improvement before promoting a richer incidence model.

Reject:
promoting a latent mixture because it sounds mechanistic.

### I-03 — Width alias is not the required explanation

G0 directly broke the one-digit/two-digit alias using 8/08 and 9/09.

Transfer:
preserve representation-level alias breakers as a standard falsification technique.

### I-04 — Natural depth is spike plus tail

G-A strongly rejects one geometric depth law; depth1 dominates with a separate deep tail.

Transfer:
represent rare phenotype as at least two descriptive components.

Do not transfer:
an assertion that the fitted deep-tail law is the actual stock distribution.

### I-05 — Controlled transition is stronger than natural incidence

Primer-qualified controlled-spawn yielded 55/55 correct terminal phase patterns.

Transfer:
Q64 is a usable state anchor for controlled transition experiments.

Do not transfer:
55/55 as the frozen 72-trial reliability endpoint.

### I-06 — Observation and state are distinct

Negative memory.current deltas occur in trials whose later stock phase remains correct.

Transfer:
negative uncharge/drain emission must be modeled independently from stock consumption.

### I-07 — PTE is a real possible pre-data charge path

Source audit connects PTE allocation to memcg charging; G0 observed VmPTE growth, while controlled-spawn
preconditioning eliminated measured PTE growth.

Transfer:
VmPTE/PTE receipts and preconditioning remain first-class mechanism controls.

Do not transfer:
a deterministic universal PTE veto; the current statistical sample does not establish one.

### I-08 — pre_current is context, not stock

G-F contains a reproducible within-range pre_current association; G0 transport is unresolved.

Transfer:
retain pre_current as a contextual sensor.

Reject:
treating cgroup memory.current as a direct read of per-CPU residual stock.

### I-09 — Natural and constructed cohorts have different selection likelihoods

Natural experiments sample unknown initial state after admission.
Spawn explicitly observes a Q64 reset before controlled consumption.

Transfer:
keep separate likelihoods/estimands.

Reject:
pooling natural incidence and primer-qualified reliability into one Bernoulli population.

### I-10 — Receipts are part of the scientific result

CPU, VmPTE, THP/mTHP, manifest, environment and artifact receipts repeatedly changed interpretation.

Transfer:
new abstractions must define their receipt before their policy.

## External evidence atoms

### E-01 — Linux page_counter-stock v6 is an abstraction move, not yet a policy transition

The earlier v5 combined implementation relocation and behavior changes.
v6/resend retains the seven-slot per-CPU design and drain policy while moving stock abstraction toward page_counter.

Transfer:
split "implementation owner" and "stock policy" in kernel receipts.

Reject:
assuming a changed rare-state distribution merely from the stock struct moving.

### E-02 — Linux tiered memcg limits separates footprint from placement entitlement

The RFC proposes per-tier counters/limits and tier-aware allocation/reclaim/migration policy.

Transfer:
"total bytes" and "fast-tier entitlement" are separate resource dimensions.

Status:
research branch only; not current mainline semantics.

### E-03 — Strata demonstrates topology before total capacity

A global expert-cache admission topology can waste capacity even when slot count is sufficient.

Transfer:
allocation topology is a state variable.

### E-04 — Strata demonstrates phase leasing

Expert-cache VRAM can be temporarily borrowed by prompt scratch and returned/refilled later.

Transfer:
ownership/lease is independent from physical tier.

### E-05 — Strata demonstrates a staging knee

Deeper pinned staging improves overlap until it steals too much scarce memory from the working set.

Transfer:
buffer/staging depth should be searched for an interior optimum, not maximized.

### E-06 — Strata demonstrates bottleneck migration

After expert residency saturates, per-stage GPU latency dominates; a slower extra device can hurt.

Transfer:
optimization must detect the active bottleneck regime.

### E-07 — mzCache makes restoration cost first-class

Partial eviction is designed around cheap restoration from arbitrary states.

Transfer:
two equally cold states are not equivalent if restoration cost differs.

### E-08 — vLLM tiered KV treats lower tiers as persistent cache, not just spill

Host, filesystem, object store and peers form a reload path that can beat recomputation.

Transfer:
lower-tier hit cost and recomputation cost must be distinct.

### E-09 — TierKV uses predicted future demand

Placement decisions are made using expected future cache demand rather than reactive eviction alone.

Transfer:
next-use prediction is a candidate controller input.

### E-10 — SSD-LLaMA makes SSD an active execution tier

SSD/RAM/VRAM are coordinated for dynamic expert delivery.

Transfer:
lower tiers may participate in execution scheduling rather than act only as passive overflow.

### E-11 — Cache-aware MoE routing changes demand itself

The routing policy can be adapted to reduce future memory traffic.

Transfer:
demand shaping is a possible action, not only placement.

Scope:
application layer, not finite-ram core.

### E-12 — External convergence is architectural, not mechanistic validation

Strata, mzCache, vLLM, TierKV, SSD-LLaMA and tiered-memcg work all separate placement, transition cost and
future use.

Transfer:
general state-transition abstraction.

Reject:
using this convergence as evidence that the Q64 mechanism is universal.

# Council rounds

## Round 1 — One unified model or layered model?

### Conflict

Systems role wanted one universal memory-state model.
Statistics and measurement roles objected that natural rare incidence and controlled-spawn have different
selection processes.

### Resolution

Use a layered model:

- natural-incidence predictor;
- kernel mechanism/observation model;
- generic residency-control model;
- application-specific policy adapters.

**Converged: 7/7 roles.**

## Round 2 — What is the canonical natural predictor?

### Conflict

Mechanism role preferred a latent-stock mixture.
Statistics role pointed out that the mixture does not improve held-out prediction and is not physically identified.

### Resolution

CAP10+ step remains the baseline predictor.
The stock model remains a mechanism sketch anchored by direct Q64 experiments, not a replacement incidence model.

**Converged: 7/7 roles.**

## Round 3 — How much of external AI-memory work enters core?

### Conflict

AI-runtime role proposed importing tiering, prediction and demand shaping into one controller.
Maintainer and falsification roles flagged scope explosion and model-specific contamination.

### Resolution

Absorb only cross-domain invariants into the generic control state:

- tier;
- owner/lease;
- hotness;
- predicted next use;
- transfer cost;
- restoration cost;
- interference;
- bottleneck regime.

Specific algorithms remain isolated BORROW candidates.

**Converged: 6/7 initially, 7/7 after promotion rule was added.**

## Round 4 — How to treat Linux page_counter-stock evolution?

### Conflict

The B388 v5 reading predicted a behavioral kernel-generation boundary.
Fresh v6 evidence shows the series deliberately preserves seven-slot/drain semantics.

### Resolution

Do not encode kernel version or implementation location as behavior.

Introduce a semantics receipt with separate fields for:

- implementation owner;
- stock topology/policy;
- batch size;
- drain policy;
- tiered-limit state.

The B388 statement was corrected.

**Converged: 7/7.**

## Round 5 — What should finite-ram-lab become?

### Candidate A

Stay only a memcg/Q64 lab.

Rejected as too narrow: the evidence already produced transferable finite-resource principles.

### Candidate B

Become an LLM memory runtime.

Rejected as scope drift and premature productization.

### Candidate C

Become a finite-resource state-transition research lab, with Q64 as the deepest kernel case study and separate
generic/application lanes.

Accepted.

**Final convergence: 7/7.**

# Final transfer classification

## ABSORB NOW

### A1 — Dual-model contract

Maintain:

- natural incidence baseline;
- mechanism/transition model.

Never silently merge them.

### A2 — Kernel memory semantics receipt

Added:

schemas/KERNEL-MEMORY-SEMANTICS-RECEIPT-v1.schema.json

This separates implementation owner from behavioral stock policy.

### A3 — Observation-contamination state

Negative uncharge/drain emission becomes a first-class observation label.

### A4 — Generic finite-memory control state

Added:

docs/FRL-STATE-TRANSITION-MODEL-v0.md

Core dimensions:

- physical tier;
- owner/lease;
- hotness;
- predicted next use;
- transfer cost;
- restoration cost;
- interference;
- bottleneck regime.

### A5 — Promotion rule

An external mechanism cannot become a core abstraction until an isolated dogfood test shows:

- measurable effect;
- reproducibility;
- independence from model-specific constants;
- stable receipts;
- falsifiable counter-condition.

### A6 — Topology-before-size principle

Capacity alone is no longer an acceptable experimental independent variable when allocation topology can differ.

Every future "capacity" experiment must state whether topology/ownership changes with it.

## BORROW INTO ISOLATED RESEARCH BRANCHES

### B1 — LEASE-001

Test phase-based temporary ownership of a fixed fast-memory region.

Question:

Can bounded lease-and-return beat static partitioning at the same peak capacity?

Source inspiration:
Strata.

### B2 — RESTORE-001

Compare policies that optimize eviction footprint versus restoration cost.

Question:

Can a state with more evicted bytes still be better if its restoration path is cheaper?

Source inspiration:
mzCache and vLLM tiered KV.

### B3 — STAGING-001

Search for an interior staging-depth knee.

Question:

At what depth does overlap benefit get overtaken by working-set displacement?

Source inspiration:
Strata.

### B4 — PREDICT-001

Compare reactive placement against next-use-aware placement on a synthetic trace.

Question:

When does prediction benefit exceed misprediction/transfer cost?

Source inspiration:
TierKV.

### B5 — ACTIVE-COLD-001

Evaluate a lower tier as an active streamed execution source rather than passive backup.

Source inspiration:
SSD-LLaMA / Strata / vLLM.

### B6 — KERNEL-TIER-001

Track and, only when justified, reproduce tiered-memcg semantics.

Question:

How do per-tier accounting and placement constraints alter pressure knees and isolation?

Status:
RFC-watch branch, not current physical work.

## HOLD

### H1 — Demand shaping

Cache-aware model/router adaptation is interesting but belongs to an AI-worker application lane.

Do not add training/router adaptation to finite-ram core yet.

### H2 — Automatic multi-device placement coefficients

Borrow the cost-model shape, not Strata's empirical constants.

### H3 — New complex rare-incidence latent model

Hold until a candidate beats CAP10+ step on held-out blocks/runs or new receipts identify a latent variable.

## REJECT

### R1

"More capacity is always better."

Rejected by both internal and external evidence.

### R2

"Kernel version alone defines memory semantics."

Rejected; receipts must describe actual stock/tier policy.

### R3

"page_counter-stock v6 necessarily changes natural Q64 distribution."

Rejected based on v6 retaining existing stock policy.

### R4

"pre_current is residual stock."

Rejected.

### R5

"PTE growth universally prevents exact-zero."

Rejected.

### R6

"One latent mixture should explain natural incidence and controlled-spawn reliability."

Rejected.

### R7

"External tiering papers validate Q64."

Rejected.

# Priority after convergence

## P0 — Preserve pause

No new physical experiment from this Council.

## P1 — Integrate semantics

Done in this bounce:

- corrected v6 stock interpretation;
- kernel semantics receipt schema;
- layered state-transition model;
- Council decision ledger.

## P2 — Next core question when research resumes

Resolve observation cleanliness before reliability scaling:

- identify the -17/uncharge source;
- distinguish charge emission from asynchronous uncharge;
- preserve Q64 primer semantics.

Do not spend the next run merely adding more b63 samples before the observer is cleaner.

## P3 — First generic finite-memory dogfood

If a non-Q64 branch is opened, start with LEASE-001 or STAGING-001.

Reason:

- they require no model training;
- can be synthetic;
- have direct falsifiable controls;
- test a cross-domain invariant rather than copying an application.

## P4 — Watch kernel tier semantics

Monitor:

- page_counter-stock v6+;
- tiered memcg limits RFC.

Do not run a cross-kernel comparison until a behaviorally relevant semantic difference is actually present.

# Council conclusion

finite-ram-lab should be defined as:

> **a laboratory for discovering, measuring, and controlling hidden state transitions under finite memory/resource constraints.**

Q64/memcg remains the deepest kernel-level case study.

External AI-memory systems contribute reusable control dimensions, not evidence for the Q64 mechanism.

The lab should expand by isolated, receipt-first experiments rather than by importing entire runtimes.
