# FR-META-002 — Research Method Telemetry Observation Plane

Status: **SYNTHETIC OBSERVATION SCHEMA / DOGFOOD PREPARATION**

Parent: **FR-META-001**

## Question

FR-META-001 can compare research protocols recursively, but its first L1/L2
cost-and-gain distributions are synthetic.

The next shortest path to the North Star is therefore not another optimization
rule. It is an observation plane for the research process itself.

The observation plane asks which research protocol moves a measured North-Star
gap with the least operational friction while preserving decision quality,
rare-failure capture, provenance, and authority boundaries.

## What is observed

Only durable or explicit operational metadata is eligible:

- bounce identifier;
- selected protocol and gap class;
- external tool-call count;
- maximum calls between user-visible progress updates;
- number of files used to rehydrate;
- rehydrate bytes when available;
- durable transitions produced;
- Monte Carlo trial budget;
- failure specimens captured;
- branches opened / closed;
- North-Star gap before / after when already explicitly measured;
- explicit stop reason;
- explicit claim class;
- whether authority expanded.

These fields describe process behavior, not private reasoning content.

## What is deliberately not observed

FR-META-002 must never require or reconstruct:

- private chain-of-thought;
- hidden reasoning tokens;
- latent model activations;
- invented telemetry for legacy bounces.

Missing fields remain **UNKNOWN**. They are not converted to zero.

UNKNOWN calls are not zero calls. UNKNOWN MC budget is not zero MC budget.
UNKNOWN frontier movement is not no movement.

## Existing operational contracts reused

The repository already froze:

- six external calls as the default maximum before a durable checkpoint;
- three calls between user-visible progress updates;
- a fresh-bounce read set of CURRENT + canonical input + at most three
  additional files;
- one durable transition per atomic micro-bounce.

FR-META-002 observes compliance with those contracts. It does not silently
redefine them.

## Event assessment

Each event is classified as OK, REVIEW, CRITICAL, or
INSUFFICIENT_TELEMETRY.

Signals include:

- external-call budget exceeded;
- progress-update budget exceeded;
- rehydrate-file budget exceeded;
- non-atomic durable transition;
- branch-sprawl signal;
- authority expansion.

Authority expansion is CRITICAL.

Missing telemetry is not treated as a violation, but sufficiently incomplete
critical telemetry becomes INSUFFICIENT_TELEMETRY.

## Synthetic fixtures

The frozen first panel contains:

1. LEAN-001 — bounded calls, bounded rehydrate set, one durable transition,
   and measured frontier movement.
2. MC-001 — exactly the six-call budget, explicit 5,000-trial MC spend,
   failure specimens retained, and one durable transition.
3. STALL-001 — eight calls, oversized rehydrate set, no durable transition,
   three branches opened without closure, and runtime-loss stop reason.
4. UNKNOWN-001 — a legacy partial record whose missing values remain UNKNOWN
   rather than becoming an apparently cheap bounce through zero imputation.

These fixtures are schema and alert-logic tests only.

## Monte Carlo on the protocol itself

The existing six-call checkpoint threshold is also allowed to become a research
question.

FR-META-002 performs a synthetic sensitivity sweep for thresholds 4 through 8
under two deliberately overlapping toy distributions: safe bounces and
stall-prone bounces.

For each threshold it reports safe-bounce flag rate, stall miss rate, balanced
loss, false-positive-heavy loss, and stall-miss-heavy loss.

The purpose is not to select a new threshold. The purpose is to prove a
meta-meta rule: the preferred research-process threshold depends on the loss
function and must not be silently optimized against a synthetic assumption.

Therefore the frozen decision is:

    NO_THRESHOLD_CHANGE_FROM_SYNTHETIC_ONLY

Real dogfood telemetry plus a fresh Council is required before changing the
six-call rule.

## Aggregation semantics

Aggregates always carry value, observed count, total count, and coverage.
This prevents a method from looking efficient merely because expensive events
failed to report telemetry.

Branch delta and frontier movement likewise record how many events were actually
observable.

## How this closes the next recursive gap

The intended flow is:

    future canonical bounce
      -> emit explicit method telemetry
      -> aggregate observed cost / gain / failure capture
      -> fit empirical L1 distributions
      -> rerun FR-META-001 protocol comparison
      -> holdout + perturb + Goodhart audit
      -> Council
      -> bounded protocol revision

Then L2 receives the same treatment: evaluator revisions are measured for
downstream calibration, reversals, and missed failures before promotion.

## First dogfood metrics worth accumulating

The most useful early fields are:

- tool calls per durable transition;
- rehydrate bytes/files per durable transition;
- Monte Carlo trials per research decision;
- failure specimens captured per experiment;
- branches opened minus branches closed;
- later theory reversals per prior decision;
- frontier movement per closed gap;
- runtime-loss / stale-active incidence.

No single metric is the objective.

The North Star remains the Qualified Task Survival Frontier; these are
research-process costs and reliability signals.

## Authority boundary

FR-META-002 is observation-only. It does not authorize local host execution,
kernel mutation, paid compute, automatic sample expansion, automatic workflow
reruns, automatic branch deletion, automatic modification of the six-call rule,
or live memory-policy promotion.

## Claim ceiling

**SYNTHETIC_METHOD_TELEMETRY_SCHEMA_AND_ALERT_LOGIC_ONLY**
