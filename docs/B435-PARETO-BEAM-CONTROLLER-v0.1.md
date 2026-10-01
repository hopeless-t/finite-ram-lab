# B435 — Pareto Beam Controller v0.1

Status: **synthetic heuristic-versus-exact evaluation**. No physical benchmark ran.

## 1. Motivation

B434 provides an exact oracle for tiny bounded windows, but exact enumeration grows as the product of option counts.

B435 adds a bounded beam search that attempts to preserve the local Pareto frontier while avoiding full enumeration.

The design goal is conservative:

> prefer returning a subset of the true frontier over returning dominated or unsafe plans.

## 2. Algorithm

At each semantic-state option group:

1. expand every current beam plan with every safe option;
2. reject per-tier capacity violations immediately;
3. compute the partial Pareto frontier;
4. if the partial frontier fits inside the beam, keep all of it;
5. otherwise:
   - preserve one extreme point for each objective dimension;
   - fill the remaining beam slots by a pressure-aware score.

The final result is the Pareto frontier of the retained beam.

## 3. Why partial Pareto pruning is lossless

At one prefix depth, all partial plans face the same remaining option groups.

If partial plan A dominates partial plan B on every additive objective, then adding the same future option vector F preserves dominance:

A + F <= B + F.

Therefore a dominated prefix cannot become globally non-dominated later.

The only heuristic step is truncating a partial frontier that exceeds the beam width.

## 4. Pressure-aware truncation

The pruning score combines:

- squared capacity ratio per tier;
- normalized tier byte-seconds;
- normalized traffic;
- normalized compute;
- normalized latency;
- normalized error.

The squared pressure term raises the cost of approaching a tier capacity cliff.

The score is used only to decide which additional partial Pareto points survive truncation.

It does not choose a final winner.

## 5. Preserving extremes

Before scalar pressure ranking, the truncation step retains one best point for every objective dimension.

This protects alternatives such as:

- minimum VRAM;
- minimum RAM;
- minimum traffic;
- minimum compute;
- minimum latency;
- minimum error.

Without this step, a scalar pruning score can easily erase an important frontier arm.

## 6. Evaluation corpus

Frozen in:

- analysis/inputs/B435-PARETO-BEAM-EVAL-v0.1.json

Deterministic seed:

- 435300

Generated:

- 1,000 synthetic instances;
- 2..5 semantic states;
- 2..5 safe options per state;
- independent RAM/VRAM capacities 15..50.

695 instances had a non-empty exact feasible frontier.

Across those instances:

- exact frontier points total = 11,408.

All options were marked semantically safe in this stress corpus so the measurement focuses on approximation loss rather than safety filtering.

## 7. Recovery results

| Beam width | Exact frontier point coverage | Approx points dominated by exact | Max domination gap |
|---:|---:|---:|---:|
| 8 | 35.68% | 0.221% | 0.660 |
| 16 | 56.28% | 0.0156% | 0.0462 |
| 32 | 76.02% | 0.0346% | 0.385 |
| 64 | 91.34% | 0% | 0 |
| 128 | 98.34% | 0% | 0 |
| 256 | 99.81% | 0% | 0 |

Interpretation:

- beam 64 missed some exact frontier points;
- every point it did return in this corpus was itself an exact frontier point;
- beam 128 recovered nearly all exact frontier points;
- beam 256 was effectively exact for this problem-size distribution.

This is synthetic evidence only.

## 8. Domination gap

For an approximate plan a and exact frontier point e, B435 defines a normalized positive-excess gap:

max_i max(0, (a_i - e_i) / max(1, |e_i|)).

The plan gap is the minimum of that quantity over the exact frontier.

A zero gap means the approximate plan is not worse than some exact frontier point on every objective.

Because every approximate plan is drawn from the exact candidate space, a zero gap together with exact non-domination means it is itself an exact Pareto point, modulo duplicate objective vectors.

## 9. Safety properties retained from B434

Beam search never weakens semantic safety.

Before expansion:

- unproven release is rejected;
- unproven owner merge is rejected;
- lossy state with unknown error bound is rejected.

During expansion:

- per-tier capacity violations are rejected.

Therefore beam width can reduce frontier coverage, but it cannot legalize an unsafe option.

## 10. Validation

Frozen files:

- src/finite_ram_lab/pareto_beam_controller.py
- tests/test_pareto_beam_controller.py
- analysis/inputs/B435-PARETO-BEAM-EVAL-v0.1.json
- docs/B435-PARETO-BEAM-CONTROLLER-v0.1.md

Authoring validation:

- large beam equals exact on 1,000 deterministic small random problems: PASS;
- unsafe-only option group returns no plan: PASS;
- tier capacities remain independent: PASS;
- exact self-recovery metrics return coverage 1 / gap 0: PASS;
- 5,000 width-64 random outputs remain capacity-feasible and internally non-dominated: PASS;
- fixed 1,000-instance all-safe benchmark produced the table above.

Claim ceiling:

SYNTHETIC_HEURISTIC_VS_EXACT_ORACLE.

## 11. What B435 changes

The control architecture is now practical enough to study larger windows:

semantic proof gate
-> tier feasibility
-> partial Pareto prune
-> bounded beam
-> approximate Pareto frontier.

This is materially better suited to Live-State Frontier than a one-score greedy scheduler because it preserves competing trade-off arms until the beam bound forces compression.

## 12. Next bounce B436

The next useful step is to stop using random abstract options and feed the controller one **source-backed mixed scenario** assembled from earlier bounces.

Candidate scenario:

- Strata INT8 KV: full residency vs streamed residency;
- Strata expert state: GPU/RAM/file alternatives;
- prompt phase: cache borrowing;
- idle phase: unload;
- one FlashAttention-style semantic reduction opportunity;
- one GEMMul8-style temporalization option.

Keep all quantities either:

- source-backed;
- measured;
- or explicitly normalized.

Then ask:

1. which plans are infeasible on a small-VRAM / finite-RAM machine;
2. which Pareto arms survive;
3. which decisions change near a VRAM or RAM capacity cliff;
4. whether the beam controller recovers the exact mixed frontier.
