# News Intake 2026-10-02 — Context Language Models and Low-Interference Cognition

Status: RESEARCH INTAKE / NO CLAIM OF LOCAL REPLICATION

## Why this belongs in finite-ram-lab

Context Language Models (CLMs) turn a long-horizon agent's context from an append-only
transcript into a model-managed finite working set. That is structurally close to the
finite-RAM problem, but not identical: evicting a RAM page should normally preserve
program semantics, while deleting or summarizing context can change the model's future
distribution.

The useful bridge is therefore not "context is RAM". It is:

> Context is a finite resident information surface with pressure, locality, eviction,
> stale representations, and task-dependent semantic loss.

Primary sources captured 2026-10-02:

- Context Language Models: https://arxiv.org/abs/2609.37725
- Official implementation: https://github.com/facebookresearch/context-language-models
- Harness Learning: https://arxiv.org/abs/2609.35738
- Pi Durable cross-reference: https://earendil.com/posts/pi-durable/

The official CLM repository reports zero-shot improvements while using fewer FLOPs,
and exposes a harness where the editable conversation is mirrored to
`/tmp/.live_ctx/LIVE_CTX_MAIN.txt`. The system/task prefix is re-pinned and protected;
the editable working region can be summarized or deleted. The harness also has explicit
budget nudges, rollback-on-overflow, and fit/shrink edit gates.

These are source observations, not finite-ram-lab replication results.

## Atomic decomposition

### Atom A — resident context is a selected set, not the whole history

Let the complete available history at turn t be H_t and the resident context be
S_t subseteq H_t under token budget B.

The ordinary append-only regime approximates:

    S_{t+1} = truncate(S_t + observation_t)

A CLM-like regime instead exposes a policy:

    S_{t+1} = pi_ctx(H_t, S_t, observation_t, B)

The research object is pi_ctx, not merely compression ratio.

### Atom B — context eviction is semantically lossy

For physical memory, reclamation can often be modeled as changing residency while
preserving logical state. For context:

    P(y | S_t) != P(y | S_t \ removed_chunk)

in general.

Therefore a context governor needs at least four costs:

1. resident compute/token cost,
2. omission loss,
3. interference from irrelevant/superseded material,
4. stale-state error when cached representations are reused after edits.

### Atom C — immutable contract and mutable cognition should be distinct planes

The CLM harness protects the system/task prefix and only exposes later turns to editing.
That suggests a stronger general invariant for agent systems:

    IMMUTABLE CONTRACT != MODEL-MANAGED WORKING CONTEXT

Candidate immutable material:
- authority grants,
- execution receipts,
- canonical evidence identifiers,
- system/task contract.

Candidate mutable material:
- scratch reasoning,
- search dead ends,
- superseded tool output,
- summaries,
- hypotheses.

### Atom D — compaction has rewrite locality

The CLM harness notes that an early edit forces the suffix after the edit to be re-read.
So edit cost is a function of position, not only bytes removed.

For an edit at position p in context length L:

    rewrite_cost(p) ~ suffix_mass(p..L)

This creates a scheduling problem analogous to write amplification and cache invalidation.

### Atom E — Suffix Cache Reuse creates a staleness problem

After a prefix edit, the exact hidden representation for a later token should change.
If old suffix state is reused, then for a small perturbation:

    Delta h_j ~= J_{j,p} Delta x_p

and therefore:

    ||Delta h_j|| <= ||J_{j,p}|| ||Delta x_p||

This is not a claim that transformer dynamics are globally linear. It gives a local
measurement target: edit magnitude and edit position should be swept against hidden/logit
drift and task correctness.

## Working mathematical model

Define one context state S with:

- Q(S): task utility / correctness,
- C(S): compute and token cost,
- L(S): information lost through compaction,
- I(S): interference from resident but irrelevant material,
- D(S): stale-cache divergence after edits.

A candidate objective is:

    J(S) = Q(S)
           - lambda * C(S)
           - mu * L(S)
           - nu * I(S)
           - xi * D(S)

This is deliberately multi-objective. A single "compression ratio" is insufficient.

### Toy knee check

For a purely illustrative diminishing-return model:

    U(k) = 1 - exp(-k/8)
    Cost(k) = lambda*k + 0.6*(k/64)^2
    J(k) = U(k) - Cost(k)

with k in [0,64], exhaustive integer sweep gives:

- lambda=0.005 -> optimum k=20
- lambda=0.010 -> optimum k=17
- lambda=0.020 -> optimum k=13
- lambda=0.040 -> optimum k=9

These are not empirical CLM values. They establish that once marginal context utility
decreases while residency/interference costs increase, a finite interior working-set
optimum exists and moves predictably with pressure price.

## Falsifiable hypotheses

### FR-CLM-H1 — Context Pressure Knee

There exists a task/model-specific context-residency knee K_ctx such that reducing
resident context above K_ctx has negligible correctness cost, while crossing below
K_ctx causes a discontinuous rise in failures or re-exploration.

Falsifier: correctness degrades smoothly with no identifiable knee across replicated
runs and seeds.

### FR-CLM-H2 — Interference Knee can precede capacity pressure

For some long-horizon tasks, adding stale/superseded context beyond a threshold reduces
task success before the hard context limit is reached.

Falsifier: resident-context growth has no negative effect after controlling for compute.

### FR-CLM-H3 — Edit position matters independently of edit size

For equal removed-token counts, early edits cause higher recompute/cache-staleness cost
than late edits.

Falsifier: position has no measurable effect after matching semantic edit magnitude.

### FR-CLM-H4 — Suffix cache reuse has a staleness knee

There is a boundary in edit magnitude/location/reuse depth where reuse remains
task-equivalent, followed by a sharp increase in logit divergence or task error.

Falsifier: error is either always negligible or monotonic without a reproducible knee.

### FR-CLM-H5 — Harness adaptation can improve fixed-model utility

Holding model weights and task corpus fixed, a feedback-trained or iteratively revised
context harness can improve success/cost Pareto position.

Falsifier: gains disappear on held-out tasks or are explained by added model/search
compute rather than harness changes.

## Proposed experiment sequence

### FR-CLM-001 — Vanilla vs heuristic compaction vs self-managed context

Arms:
- append/truncate baseline,
- deterministic heuristic summarizer,
- CLM-style editable context.

Freeze:
- model,
- task corpus,
- tool surface,
- seed schedule where possible,
- max LM calls.

Measure:
- exact/task score,
- total input tokens,
- FLOPs or cost proxy,
- resident-token trace,
- compaction count,
- re-exploration events,
- premature branch termination,
- wall time.

### FR-CLM-002 — Pressure sweep

Sweep resident budget B over a geometric/locally refined grid.
Use the existing finite-ram-lab methodology:

    coarse sweep -> suspected knee -> local refinement -> replication -> failure biopsy

Do not infer a universal K_ctx from one model/task family.

### FR-CLM-003 — Failure-state biopsy

At the first failing turn retain:
- pre-edit context,
- post-edit context,
- removed spans,
- summary spans,
- next model request,
- tool observation,
- correctness delta.

Classify:
- essential evidence removed,
- stale evidence retained,
- contradiction/interference,
- excessive rewrite cost,
- cache-staleness candidate,
- unrelated model error.

### FR-CLM-004 — Context Staleness Knee

Reference arm: exact re-prefill after every edit.
Treatment arm: suffix-cache reuse.

Sweep:
- edit position percentile,
- edit token count,
- semantic importance class,
- number of consecutive reuse cycles.

Measure:
- KL/logit drift where observable,
- task exactness,
- latency,
- FLOPs,
- cache hit/reuse fraction.

### FR-CLM-005 — Rare-event capture

Use the finite-ram-lab Rare Event workflow. Keep successful and failed edit trajectories
in JSONL and search for low-frequency catastrophic forgetting or false-confidence cases.

## Connection to current finite-ram-lab work

B494-B500 already develop a bounded, calibrated Governor with:
- exploration,
- Pareto selection,
- evidence-efficient extension,
- host binding,
- promotion only after sufficient local evidence.

The CLM intake should reuse the methodology, not import existing q thresholds.
A context governor must be independently calibrated per model/runtime/task environment.

Potential future Governor state:

    context pressure
        -> candidate compaction policies
        -> local Pareto
        -> host/model/task fingerprint
        -> evidence-bound policy

Do not use hosted-runner thresholds as development-machine policy.

## Cross-repository dispatch

- mvca: protect immutable authority/evidence from model-managed context edits.
- mvca-hq / KITten Circuit: compare fixed kittens under different context harnesses.
- catfood-jev-cua-lab: use bounded decision heads/calibrators to score compaction risk.
- finite-tool-surface-lab: unify context residency and tool-schema residency as related,
  but separately measured, working-set problems.

## Claim ceiling

Current claim is only:

    CLM_FINITE_WORKING_SET_RESEARCH_HYPOTHESES_DEFINED

No local CLM benchmark, no Suffix Cache Reuse replication, and no general causal
performance claim is made by this intake.
