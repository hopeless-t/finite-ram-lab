# FR-META-001 — Recursive Research Improvement Loop

Status: **SYNTHETIC METHOD EXPERIMENT / META-META GOVERNANCE**

Parent: **FR-NORTHSTAR-005**

## What existed already

Finite RAM Lab already had strong partial closed loops: atomic micro-bounces, pseudo-Council review, Monte Carlo sizing and rare-event search, failure biopsy, theory updates, the primitive registry, causal shadow replay, gap-driven experiment selection, and North-Star frontier re-evaluation.

FR-NORTHSTAR-005 closes the object-level loop: frontier miss -> gap classification -> justified experiment -> primitive/effect-model update -> frontier re-evaluation -> branch stop when the gap closes.

What was missing was a loop whose experimental object is **the research method itself**.

## L0 — object-level research

Default sequence:

    explore
      -> atomize
      -> pseudo-Council
      -> Monte Carlo when it buys decision value
      -> experiment
      -> failure biopsy when the observed state requires it
      -> theory update
      -> primitive registry update
      -> frontier re-evaluation

The historical sequence is preserved as a safe baseline, but Monte Carlo and biopsy are now explicitly eligible for value-of-information routing rather than being ritual steps.

## L1 — meta loop

The L1 object is the L0 protocol. Protocol parameters become experiment candidates: gap routing, MC threshold, biopsy threshold, stop conditions, and per-gap protocol selection.

A protocol is not promoted merely because it is faster. It must pass decision-quality, rare-failure capture, frontier-progress, cost, held-out-gap, and invariant gates.

The first candidate is MIXED_V3:

| Gap class | Protocol |
|---|---|
| EVIDENCE_GAP | VOI_ADAPTIVE_V2 |
| MODEL_GAP | FIXED_V1 |
| CAPABILITY_GAP | FIXED_V1 |
| CONTRACT_GAP | VOI_ADAPTIVE_V2 |
| FRONTIER_REACHED | VOI_ADAPTIVE_V2 |

The key point is selective improvement: the meta loop does not globally replace the full pipeline where the full pipeline still has value.

## L2 — meta-meta loop

The L2 object is the L1 evaluator. It asks whether the mechanism choosing a better research protocol is itself robust or merely optimizing an arbitrary score.

Three controls are mandatory:

1. **Held-out gap.** CAPABILITY_GAP remains FIXED_V1 and must be bit-for-bit identical under the frozen seed.
2. **Objective perturbation.** Frontier progress, correctness, rare-state capture, and research-cost weights are perturbed across Monte Carlo trials. Promotion must survive the ensemble.
3. **Goodhart negative control.** RISKY_FAST deliberately skips Council and treats missing evidence as zero. It is never promotable even if a scalar score ever looks attractive.

Thus metric improvement is not method improvement unless invariant, holdout, robustness, and falsifier gates all pass.

## Frozen synthetic panel

At the frozen seed:

| Metric | FIXED_V1 | MIXED_V3 |
|---|---:|---:|
| Mean research cost | 32.6 | 29.0 |
| Correct decision rate | 0.92375 | 0.91600 |
| Rare capture rate | 0.93500 | 0.87700 |
| Mean frontier progress | 0.71962 | 0.71653 |
| Mean utility | 0.31887 | 0.45128 |

These are synthetic method-model values, not empirical productivity claims.

The narrow result is that a recursive protocol selector can reduce modeled research cost while keeping predeclared correctness, rare-event, progress, holdout, and robustness guardrails satisfied.

## Pseudo-Council

The method Council has five roles: methodologist, statistician, systems researcher, falsifier, and continuity reviewer. Promotion requires unanimous convergence under the frozen gates.

Council promotion applies only to a **research-protocol candidate**. It never grants local host execution, paid resource use, kernel mutation, sample expansion outside a frozen contract, or primitive live promotion.

## Non-negotiable invariants

1. UNKNOWN is not success.
2. Missing evidence is not zero.
3. Evidence and decision remain separate.
4. Experiment requires Council and a frozen contract.
5. Failure specimens are not erased.
6. Method improvement does not expand execution authority.

A future meta-meta study may propose changing an invariant only as an explicit governance research question. It may never silently mutate one.

## Bounded recursion

L0 improves the research object. L1 improves L0. L2 audits and improves L1. Each promoted change is versioned, reversible, evidence-scoped, and re-evaluated against the same Qualified Task Survival Frontier.

There is deliberately no unbounded autonomous self-rewrite authority.

## Next dogfood step

Collect real method telemetry from future bounces: external tool calls per durable finding, experiments opened per closed gap, Monte Carlo trials per decision, captured failure specimens, later reversals, rehydrate bytes/tokens, branch-sprawl count, and North-Star frontier movement.

Once enough traces exist, replace the synthetic L1/L2 cost-and-gain model with observed distributions and rerun the recursive selector. That converts FR-META-001 from a synthetic governance proof into a dogfooded research-operations experiment.

## Claim ceiling

**SYNTHETIC_RECURSIVE_RESEARCH_METHOD_SELECTION_ONLY**
