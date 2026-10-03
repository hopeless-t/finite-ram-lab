# KSLA-003 — Real-State Bounded Idiocy

Status: **SYNTHETIC REAL-STATE FINITE-VIEW EXPERIMENT**

This lane leaves the reward-table toy model.

The solver now owns an actual 256-coordinate state and must reach an exact
sparse integer target.

## Expert contract

An expert lane has only eight resident coordinates.

Each round it exhaustively tests six allowed steps on those eight coordinates
and returns its best improving local action.

This is intentionally expensive but informed:

`8 coordinates × 6 steps = 48 candidate evaluations per expert lane per round`.

When all resident coordinates are exhausted, the expert can perform a global
refresh that scans all 256 coordinates and six steps:

`1536 evaluation units`.

## Idiot contract

An idiot proposal knows nothing.

It selects one global coordinate and one step from the same frozen random tape.

Cost:

`1 candidate evaluation`.

If an idiot discovers an improving cold coordinate, the validator accepts the
action and the coordinate can become resident for the expert if more work
remains there.

Thus the idiot acts as a cheap cold-state discovery source.

## Policies

- EXPERT_HEAVY: two expert lanes, no idiots.
- EXPERT_ONLY: one expert lane.
- FIXED_LOW: one expert + three idiots every round.
- FIXED_HIGH: one expert + eight idiots every round.
- STALL_ADAPTIVE: one expert; 32 idiots only when the expert has no improving
  resident action.
- IDIOT_ONLY: sixteen idiots per round.

All 512 episodes share matched problem and random-action identities.

## Frozen results

| policy | success | mean rounds | mean work | refresh work | resident coords |
|---|---:|---:|---:|---:|---:|
| EXPERT_HEAVY | 512/512 | **46.084** | 9032.06 | 4608 | 16 |
| EXPERT_ONLY | 512/512 | 77.992 | 12959.63 | 9216 | 8 |
| FIXED_LOW | 512/512 | 75.514 | 12416.20 | 8565 | 8 |
| FIXED_HIGH | 512/512 | 70.863 | 10685.34 | 6717 | 8 |
| **STALL_ADAPTIVE** | **512/512** | 73.256 | **8169.34** | **3636** | **8** |
| IDIOT_ONLY | 384/512 | 414.219 | 6627.50 | 0 | 0 |

The adaptive mixed policy is not the fastest.

EXPERT_HEAVY remains the lowest-depth policy.

But STALL_ADAPTIVE:

- preserves 100% success in the frozen 512 episodes;
- reduces mean work by about 9.55% versus EXPERT_HEAVY;
- reduces global-refresh work by about 21.1%;
- uses half the expert resident coordinates;
- discovers about 31 cold coordinates per episode through ignorant proposals.

This is the first real-state experiment in the KSLA chain where deliberately
admitting ignorance improves a finite-resource objective relative to a heavier
expert portfolio.

## Resource-price frontier

Use:

`J = mean_work_cost + lambda_round * mean_rounds`.

The break-even between STALL_ADAPTIVE and EXPERT_HEAVY is approximately:

`lambda_round = 31.7504 work units per serial round`.

Therefore:

- if serial latency is priced below that value, STALL_ADAPTIVE is cheaper;
- if serial latency is priced above it, EXPERT_HEAVY is worth its extra work
  and residency.

So the correct conclusion is not:

`idiots beat experts`.

It is:

`stall-gated cheap ignorance can beat additional expert residency when global
refresh and resident expertise are expensive enough`.

## Negative controls

Pure idiot search has the lowest average work among the listed policies, but it
only solves 384/512 episodes within the 500-round deadline.

It therefore fails a 100% frozen reliability floor.

Fixed low/high idiocy both lose to stall-gated idiocy on work in this fixture.

This supports adaptive idiocy rather than indiscriminate randomness.

## Claim ceiling

**SYNTHETIC_REAL_STATE_FINITE_VIEW_EXPERIMENT_ONLY**

This is not a claim against CG, Kaczmarz++, or general numerical solvers.

It is a finite-resident-view systems experiment.
