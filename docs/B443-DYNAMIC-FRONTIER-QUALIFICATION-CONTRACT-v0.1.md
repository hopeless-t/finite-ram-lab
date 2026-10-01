# B443 — Dynamic Frontier Qualification Contract v0.1

Status: **qualification contract only**. No new physical capacity sweep ran.

## 1. Why this contract exists

B438 provides a static capacity-monotonicity theorem.

B439 provides a comparator for measured violations.

B440 supplied the first historical real capacity pair.

B441 showed that objective authority matters.

B442 showed that frontier membership stability matters.

The next physical experiment should not rediscover those failure modes after execution.

B443 freezes them as preconditions.

## 2. Required experimental identity

Every dynamic frontier study must freeze:

- one explicit capacity axis;
- at least two capacity points;
- stable plan identity fields;
- workload/model/input identity;
- objective definitions;
- independent replication unit;
- raw-receipt retention.

A comparison with changing plan semantics or changing workload identity is not a capacity-only dynamic frontier experiment.

## 3. Objective contract

Every objective is declared before promotion as:

- PRIMARY
- DESCRIPTIVE
- EXCLUDED

and records:

- optimization direction;
- measurement semantics;
- known contamination/uncertainty notes.

DESCRIPTIVE coordinates may be used for sensitivity analysis, but cannot replace missing PRIMARY evidence.

## 4. Replication contract

The study must declare:

- the independent resampling unit;
- minimum independent units per capacity cell.

B443 intentionally sets **no universal replication number**.

The correct count depends on:

- expected variance;
- heavy tails;
- measurement cost;
- desired frontier-stability threshold.

B442 demonstrates why four blocks can be inadequate for a noisy timing coordinate even when leave-one-out medians look stable.

## 5. Stability contract

Each study predeclares a frontier-stability threshold.

A measured frontier loss is promotion-eligible only if:

- all qualification gates pass; and
- the resampling-based loss/stability statistic reaches the predeclared threshold.

B443 does not declare 0.95 as a universal scientific law.

The STRATA-005 replay uses 0.95 only as an illustrative contract value.

## 6. Fail-closed qualification conditions

Return QUALIFICATION_HOLD when any of the following occurs:

- capacity matrix incomplete;
- PRIMARY objective missing;
- independent replication below the frozen study requirement;
- plan identity unstable;
- workload identity unstable where required;
- raw receipt missing where required.

A high apparent frontier-loss probability cannot override these failures.

## 7. STRATA-005 retrospective application

Retrospective contract:

Capacity axis:
- memory.high

Capacity points:
- 144 MiB
- 176 MiB

Plan identity:
- arm

PRIMARY:
- peak_ram_bytes
- memory_high_events
- pgscan

DESCRIPTIVE:
- scan_elapsed_ns

Independent unit:
- runner block

Observed units:
- 4 per capacity

Raw block receipts:
- present

Plan/workload identity:
- sufficiently frozen by STRATA-005 design for this replay

The historical dataset therefore passes the **qualification completeness** gate.

But the primary frontier-loss probability is:

0

so:

- qualification_status = QUALIFIED
- frontier_promotion_eligible = false

This distinction is important.

A dataset can be valid and complete without supporting the target effect.

## 8. Contract versus positive result

The contract separates three states that were easy to blur previously.

### QUALIFICATION_HOLD

Evidence structure is insufficient to evaluate the claim.

### QUALIFIED / NO PROMOTION

Evidence is structurally valid, but the target frontier effect is absent or below the stability threshold.

### QUALIFIED / PROMOTION ELIGIBLE

The frozen evidence structure passes and the predeclared primary frontier-stability criterion is met.

Even this final state does not identify a causal physical mechanism automatically.

It only authorizes the claim up to the experiment's frozen ceiling.

## 9. Relationship to B425

B425 remains paused.

The ambient memcg catcher is not automatically a dynamic capacity sweep.

If later used in this framework, its study contract must separately define:

- what the controlled capacity axis is;
- which ambient state constitutes one independent unit;
- which metrics are PRIMARY;
- how plan identity is preserved.

The existence of B443 does not authorize B425 execution.

## 10. Relationship to a future GPU/application sweep

A future Strata or GPU runtime experiment is a cleaner direct candidate if it exposes a bounded memory-budget knob.

Before launch, freeze:

- exact runtime/source commit;
- exact model/workload;
- capacity/residency knob;
- plan identities;
- RAM/VRAM metrics;
- transfer metric;
- latency metric if PRIMARY;
- correctness/quality metric;
- independent repetitions;
- raw receipts.

Then B439/B441/B442 can be applied without changing the analysis rules after observing the result.

## 11. Implementation

Frozen branch:

- research/dynamic-frontier-contract-b443

Files:

- src/finite_ram_lab/dynamic_frontier_contract.py
- tests/test_dynamic_frontier_contract.py
- specs/DYNAMIC-FRONTIER-QUALIFICATION-v0.1.json
- docs/B443-DYNAMIC-FRONTIER-QUALIFICATION-CONTRACT-v0.1.md

The validator checks:

- capacity matrix;
- replication;
- PRIMARY objective presence;
- stable plan identity;
- stable workload identity;
- raw receipts;
- predeclared stability threshold.

## 12. Current research boundary

The abstract side is now sufficiently instrumented to accept real observations.

The highest-value next step is no longer another taxonomy.

It is one qualified physical dynamic dataset.

Until such a dataset is explicitly launched, the current strongest real result remains:

- STRATA-005 validates the replay/qualification machinery;
- its PRIMARY projection does not violate static monotonicity;
- its timing-only apparent violation is PROJECTION_FRAGILE and block-resampling unstable.

That is a clean negative result, not a failed experiment.
