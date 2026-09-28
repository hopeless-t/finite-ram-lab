# REC-001 Recorder v0 Council

> **Status:** CONVERGED / DESIGN DECISION
> **Authority:** RESEARCH INFRASTRUCTURE ONLY

## Question

Should Finite RAM Lab insert a small evidence recorder before implementing STRATA-005, or continue the experiment pipeline first and add storage/search infrastructure later?

## Constraints

- STRATA-005's frozen causal design must not change.
- Observation must remain separate from interpretation and action.
- The recorder must not become a controller.
- Raw evidence must remain inspectable with ordinary text tools.
- The searchable store must be rebuildable from raw evidence.
- Research infrastructure must not consume more effort than the experiment it serves.

## Council

### Research methodology

**Position:** ACCEPT, but only as an observational substrate.

The number of pressure settings, arms, blocks, outcomes, provenance fields, and later cross-platform comparisons is increasing. Capturing those observations under one stable evidence contract before STRATA-005 reduces later reconciliation cost.

The recorder must not change STRATA-005 arms, thresholds, launch authority, or interpretation.

### Systems

**Position:** ACCEPT WITH GUARDRAILS.

A recorder can perturb the workload it measures through allocation, formatting, buffering, filesystem writes, locks, and scheduling. v0 therefore needs:

- monotonic timestamps;
- append-only JSONL writes;
- bounded buffering;
- no daemon;
- no network upload;
- no background policy thread;
- an explicit recorder-overhead validation before recorder-instrumented performance claims become authoritative.

### Data engineering

**Position:** ACCEPT.

Use two layers:

1. JSONL is the canonical raw observation stream.
2. SQLite is a disposable query projection rebuilt deterministically from JSONL.

Do not make SQLite the only copy of evidence. Do not make derived summaries the only retained representation.

### Statistics / reproducibility

**Position:** ACCEPT WITH SCHEMA DISCIPLINE.

Every run must be attributable to an experiment/spec/source commit and retain units. High-frequency samples must preserve a run-local sequence and monotonic time. Derived metrics must not be silently written back as measurements.

Repeated ingestion must either be idempotent or fail on conflicting duplicate identities.

### OSS maintenance

**Position:** ACCEPT ONLY THE MINIMUM.

Do not add a dashboard, server, semantic index, Parquet, DuckDB, cloud service, adaptive policy, or cross-platform abstraction in v0. Those components must earn their existence from measured needs.

### Red team

Primary risks:

- **observer effect:** recorder changes the pressure regime;
- **schema lock-in:** early assumptions become permanent;
- **dual truth:** JSONL and SQLite diverge;
- **duplicate ingestion:** aggregates silently double-count;
- **partial/corrupt tail:** crash leaves a malformed final record;
- **scope creep:** recorder becomes a memory-management product before the research supports it.

Mitigations:

- schema version on every raw record;
- JSONL remains authoritative;
- SQLite must be rebuildable;
- duplicate record identities are rejected unless identical;
- malformed JSON fails ingestion visibly;
- recorder overhead is measured before performance conclusions rely on it;
- v0 records only; it does not reclaim, protect, throttle, advise, or choose a policy.

## Convergence

**Decision: build REC-001 Recorder v0 before STRATA-005 implementation.**

This is not a replacement for STRATA-005 and does not reopen its frozen design.

The purpose is to make subsequent experiments cheaper to inspect and easier to compare while preserving raw evidence for later questions.

## v0 scope

IN:

- append-only JSONL;
- schema versioning;
- run/provenance records;
- numeric samples with units;
- discrete events;
- summaries kept explicitly distinct from measurements;
- deterministic JSONL -> SQLite ingestion;
- grep/jq-friendly raw layout;
- SQL indexes for common run/time/type queries;
- tests for round-trip, duplicate handling, and malformed input.

OUT:

- reclaim/control decisions;
- policy recommendations;
- daemon/service;
- UI/dashboard;
- network upload;
- Parquet/DuckDB;
- semantic/vector search;
- Android/iOS implementation;
- STRATA-005 launch.

## Next action

Freeze the REC-001 data contract, implement the minimal stdlib recorder/ingester, and validate it without launching STRATA-005.
