# News Intake 2026-10-02 — Agentic Meta-Reasoning as a Finite Control Working Set

Status: RESEARCH INTAKE / NO LOCAL REPLICATION

Primary source:
- Thinking Before Thinking: Scaling Agentic Inference Through Meta-Reasoning
  https://arxiv.org/abs/2609.38147

## Source observations

The paper separates object-level workers from a meta-reasoning controller. The
controller repeatedly executes four stages:

    Assess -> Propose -> Evaluate -> Dispatch

Worker outputs and controller notes live in persistent artifact memory. Between control
decisions, the controller carries a compact rewritten state rather than replaying the
full accumulated history.

The paper reports that direct-control history can exceed one million characters in long
runs while meta-reasoning controller state stays on the order of thousands to tens of
thousands of characters. The authors explicitly note that compact state is lossy and
that incorrect assessment can discard good partial work that is never re-read.

The paper also reports a low-budget crossover: staged meta-control can underperform
direct control when the allowance is small, then become beneficial as the budget grows.

These are source observations, not finite-ram-lab replications.

## Atomic decomposition

### Atom MR-FR-A — controller state is a finite semantic working set

Let M_t be persistent artifact memory and s_t the compact controller state.

The architecture can be viewed as:

    s_t = Assess(x, s_{t-1}, delta M_t ; M_t)

where M_t is not fully resident in the controller prompt. The current controller
working set is therefore a projection:

    S_t = pi_control(M_t, s_t, task, budget)

This is a second concrete instance of the finite semantic working-set problem.

### Atom MR-FR-B — memory residency and memory existence are different

An artifact may remain durably available in M_t while being absent from s_t and absent
from the selected context C_i of the next worker.

Therefore:

    EXISTS != RESIDENT != RETRIEVED != USED

This should become a first-class distinction in context-pressure experiments.

### Atom MR-FR-C — meta-control has its own pressure knee

Let:
- B be total model-call allowance,
- c_t controller calls in cycle t,
- w_t worker calls,
- b_{t+1}=b_t-c_t-w_t.

Meta-control is beneficial only if the expected improvement from better allocation and
reuse exceeds the opportunity cost of controller computation.

Define a research quantity:

    NetMetaValue(B)
      = Performance_meta(B)
        - Performance_direct(B)
        - lambda * ExtraControlCost(B)

There should exist task/model regimes where NetMetaValue(B)<0 at small B and >0 at
larger B.

This is a control-overhead knee, distinct from the context-capacity knee.

### Atom MR-FR-D — more thinking can become interference

The paper reports a chess-subset failure pattern where additional reconsideration can
destabilize an already-correct answer.

That suggests an overthinking/reconsideration hazard:

    useful_verification
        -> diminishing returns
        -> destabilization risk

This is analogous to retaining or reactivating semantically harmful state.

## New hypotheses

### FR-MR-H1 — Meta-Control Crossover Knee

For fixed model, worker interface and task distribution, there exists a budget region
B* around which explicit meta-control changes from net-negative to net-positive.

Measure:
- final task score,
- controller calls,
- worker calls,
- controller-token cost,
- wall time,
- artifact reuse,
- correct-candidate coverage,
- final selection.

### FR-MR-H2 — Resident-state size can decouple from durable-memory size

As run length grows, |M_t| may grow while |s_t| remains bounded or sublinear.

Test:

    rho_t = |s_t| / |M_t|

and compare against direct accumulated history.

### FR-MR-H3 — semantic omission risk depends on retrieval policy, not only compression

Two compact states with equal size can differ sharply in downstream success depending on
which artifact identifiers are retained or made discoverable.

### FR-MR-H4 — Reconsideration has a dose-response curve

Repeated verification/revision of an already-correct candidate can eventually reduce
the probability that it remains selected.

Candidate experiment:
- freeze a known-correct artifact,
- vary number of controller reconsideration cycles,
- prevent new task information,
- measure probability the correct candidate remains selected.

A monotonic improvement assumption should be rejected unless measured.

## Mathematical bridge to existing CLM intake

The earlier CLM objective:

    J(S)=Q(S)-lambda*C(S)-mu*L(S)-nu*I(S)-xi*D(S)

can be extended with explicit control cost and reconsideration:

    J_meta(S,B)
      = Q(S,B)
        - lambda*C_resident(S)
        - mu*L_omission(S)
        - nu*I_interference(S)
        - xi*D_staleness(S)
        - alpha*C_control(B)
        - beta*R_reconsideration(S,B)

The new terms should not be assumed independent.

## Experiment bridge

FR-CLM-001 should gain one additional arm:

    explicit staged meta-controller + persistent artifact memory

without changing the underlying worker model.

The key matched comparison should hold fixed:
- workers,
- task corpus,
- tool interface,
- nominal call budget,
- randomness schedule where possible.

This follows the paper's strongest experimental idea: change control while holding the
worker capability fixed.

## Claim ceiling

    META_REASONING_FINITE_CONTROL_WORKING_SET_HYPOTHESES_DEFINED

No reproduction of the paper's benchmark gains is claimed.
