# News Intake 2026-10-02 — LoopCD as Compute-Pressure Reuse

Status: RESEARCH INTAKE / NO LOCAL MODEL RUN

Primary source:
https://arxiv.org/abs/2610.02185

## Finite-resource interpretation

Looped Transformers decouple parameter count from effective depth by repeatedly executing
a shared block. LoopCD then reuses an intermediate recurrent state that standard decoding
would otherwise discard.

The finite-resource atom is:

    already-paid intermediate state
        -> guidance signal
        -> potentially fewer future recurrent iterations

This is not RAM reclamation, but it is resource reuse under a finite inference budget.

## Control variables

Let:
- R = full recurrent depth,
- r = executed recurrent depth,
- k = reference iteration,
- omega = guidance strength,
- C_loop = cost per recurrent step,
- C_readout = additional output cost if using logit guidance.

Approximate inference cost:

    C_hidden(r) ~= r*C_loop + C_output

    C_logits(r)
      ~= r*C_loop + 2*C_output

for the simplified physical distinction used in the paper.

The actual architecture includes fixed prelude/coda costs and must be measured per model.

## Candidate utility

    J(r,k,omega)
      = Q(r,k,omega)
        - lambda*C_compute(r,k)
        - mu*R_overshoot(omega)
        - nu*R_instability(k,omega)

This predicts a compute/guidance Pareto frontier rather than "maximum loops is best".

## New hypotheses

### FR-LOOP-H1 — recurrent depth has a pressure knee

As r increases, marginal quality gain should eventually fall below marginal compute cost.

### FR-LOOP-H2 — discarded intermediate states can have option value

An earlier state may be inferior as a standalone predictor but valuable as a contrastive
reference.

Therefore:

    low standalone quality != semantically dead state

This is directly relevant to finite-ram-lab's semantic-dead-byte/state work.

### FR-LOOP-H3 — compute can be converted into a control signal

The difference between early and late states:

    Delta_t = state_R - state_k

is produced by computation already performed.

Reusing Delta_t can reduce the amount of additional recurrent compute required to reach a
target quality level.

### FR-LOOP-H4 — adaptive intervention is a pressure governor

The top-two-margin guidance rule spends stronger intervention on uncertain tokens and
backs off on settled tokens.

This is analogous in control shape to a resource governor:
- observe pressure/uncertainty,
- intervene where marginal value is high,
- avoid unnecessary work/intervention where confidence is high.

It is an analogy, not a claim of identical dynamics.

## Proposed experiment

If a compatible looped model becomes locally available:

REFERENCE:
- full recurrent depth,
- unguided.

TREATMENTS:
- half depth unguided,
- full depth LoopCD,
- half depth LoopCD,
- adaptive-depth + LoopCD exploratory arm.

Measure:
- task score,
- forward FLOPs,
- wall time,
- peak memory,
- intermediate-state storage cost,
- per-token uncertainty,
- reference/final divergence,
- failures caused by overshoot.

Search:
- depth knee,
- guidance knee,
- joint depth/guidance Pareto front.

## Claim ceiling

    LOOPCD_COMPUTE_PRESSURE_HYPOTHESES_DEFINED

The paper's 22.5%-48.2% FLOP reductions remain upstream results.
