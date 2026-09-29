# B390 — External transfer Council converged

## Status

COUNCIL COMPLETE / NO PHYSICAL RUN.

Inputs:
- B389 MATH-014 rare-state generative model
- B388 external reconnaissance
- Strata intake
- Linux page_counter-stock v6 update
- tiered memcg limits RFC

## Main correction

B388's v5-based expectation of a stock-policy transition was too strong.

v6/resend retains:
- seven-slot per-CPU stock policy
- existing drain policy

while limiting the series to the stock abstraction move.

Therefore finite-ram-lab now records separately:
- stock implementation owner
- stock policy/topology
- batch size
- drain policy
- tier-aware memcg state

## Council convergence

Final architecture:

1. natural rare-state incidence model;
2. kernel mechanism/observation transition model;
3. generic finite-memory residency-control model;
4. application-specific adapters.

Do not merge the four layers into one likelihood or one runtime.

## Immediate absorbs

- CAP10+ step remains held-out natural-incidence baseline.
- Q64/reset stock arithmetic remains controlled-transition mechanism.
- negative uncharge/drain is first-class observation contamination.
- kernel memory semantics receipt added.
- generic control state adds:
  - tier
  - owner/lease
  - hotness
  - predicted next use
  - transfer cost
  - restoration cost
  - interference
  - bottleneck regime
- topology-before-size principle adopted.
- external mechanisms require isolated dogfood promotion.

## New files

- docs/COUNCIL-2026-09-30-FRL-TRANSFER-v1.md
- docs/FRL-STATE-TRANSITION-MODEL-v0.md
- schemas/KERNEL-MEMORY-SEMANTICS-RECEIPT-v1.schema.json

Updated:
- docs/EXT-2026-09-30-MEMORY-SYSTEMS-RECON.md

## Borrow branches

Candidate isolated branches:

- LEASE-001
- RESTORE-001
- STAGING-001
- PREDICT-001
- ACTIVE-COLD-001
- KERNEL-TIER-001

No branch is authorized for physical execution by this handoff.

## Core next priority

Before b63 reliability scaling:

resolve observation cleanliness around negative deltas / -17.

Do not merely add more samples while charge and uncharge emissions remain conflated.

## Definition after Council

finite-ram-lab:

a laboratory for discovering, measuring, and controlling hidden state transitions under finite memory/resource constraints.

Q64/memcg remains the deepest kernel-level case study.
