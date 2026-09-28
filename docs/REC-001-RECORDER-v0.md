# REC-001 Evidence Recorder v0

> **Status:** FROZEN v0 DESIGN
> **Authority:** OBSERVATION_ONLY

## Purpose

Create a small recording substrate that makes Finite RAM Lab evidence easy to preserve, grep, ingest, join, and re-analyze without choosing a memory-management policy.

The recorder implements:

```text
Observation
   |
   +--> append-only JSONL             (canonical raw evidence)
   |
   +--> deterministic SQLite projection  (query / aggregation)
```

SQLite is a projection, not the authority. Deleting the database and rebuilding it from JSONL must be a supported operation.

## Raw record contract

Each JSONL line is one JSON object.

Common fields:

- `schema_version`
- `record_type`
- `run_id`
- `seq`
- `monotonic_ns`
- `wall_time_utc`

`seq` is strictly increasing within one run.

### record_type = run_start

Carries provenance and configuration:

- experiment_id
- spec_id
- source_commit
- workflow/run/job identifiers when available
- platform/kernel/architecture metadata
- cgroup and memory-budget metadata
- workload/config object

### record_type = sample

Carries one numeric observation:

- metric
- value
- unit
- phase (optional)

### record_type = event

Carries one discrete observation:

- event
- phase (optional)
- details object

### record_type = summary

Carries one explicitly derived value:

- metric
- value
- unit
- method/details

A summary is never reclassified as a raw measurement.

### record_type = run_end

Carries completion status and optional details.

## SQLite projection

v0 tables:

- `runs`
- `samples`
- `events`
- `summaries`

Raw JSON is retained in the projection so deterministic duplicate checks do not depend on lossy field extraction.

Indexes cover common `run_id/time/type/metric/phase` queries.

## Ingestion rules

- parse every line as UTF-8 JSON;
- require a supported schema version;
- require record identity fields;
- use one transaction per input file;
- reject malformed input;
- reject conflicting duplicate `(run_id, seq)` identities;
- permit deterministic re-ingestion only when the stored raw record is identical;
- never rewrite the source JSONL;
- never infer missing provenance silently.

## Search model

The raw format intentionally remains usable with:

```bash
rg '"record_type":"event"' evidence/
jq 'select(.record_type == "sample" and .metric == "memory.current")' run.jsonl
```

SQLite exists for joins, filtering, and aggregation across runs.

## Observer-effect boundary

REC-001 is not considered measurement-transparent by assumption.

Before recorder-instrumented timing or pressure results are promoted to findings, a hosted overhead check must compare recorder-off versus recorder-on operation for:

- wall time;
- peak memory;
- pressure events;
- write volume.

No universal acceptable-overhead threshold is frozen here.

## Evolution rule

Future storage backends may be added, but must not invalidate raw v0 evidence. Schema changes require an explicit version and migration/rebuild story.

## Authority boundary

REC-001 observes and records only.

It does not reclaim, evict, pin, throttle, size a memory budget, select a cadence, or authorize a STRATA-005 launch.
