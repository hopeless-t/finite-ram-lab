# FR-META-003 — Append-only Research Method Evidence Recorder

Status: **DOGFOOD INFRASTRUCTURE**

Parent: **FR-META-002**

## Purpose

FR-META-002 defines which research-method telemetry is useful. FR-META-003
turns that schema into durable evidence that future bounces can actually
accumulate.

The design deliberately avoids one shared mutable JSONL file. Instead:

    one method event
      -> one canonical JSON file
      -> exclusive creation
      -> content SHA-256 receipt
      -> coverage-aware aggregate

This reduces write races and makes individual records independently auditable.

## Write semantics

Each event ID must be a bounded filename-safe identifier.

The recorder:

- normalizes the FR-META-002 event;
- serializes deterministic sorted compact JSON;
- creates the destination with exclusive-create semantics;
- refuses to overwrite an existing event;
- returns file name, byte length, and SHA-256.

An existing empty file is still existing evidence and blocks the write.

Event IDs cannot contain path separators or traversal sequences.

## Missing-data semantics

Null remains null.

The recorder does not fill absent telemetry with zero.

When records are aggregated, FR-META-002 reports observed count and coverage
alongside values.

This prevents an under-instrumented research path from appearing artificially
cheap.

## Read / aggregate semantics

Directory aggregation:

1. reads event files in deterministic filename order;
2. re-validates every event through the FR-META-002 normalizer;
3. passes events into the same coverage-aware aggregator;
4. emits event count and aggregate result.

The recorder does not promote aggregate output into a policy change.

## Dogfood use

Future canonical research bounces may emit method events after their durable
transition is known.

Useful fields include:

- external calls actually made;
- maximum call span between progress updates;
- rehydrate file/byte counts;
- durable transitions;
- explicit MC trial budget;
- failure specimens;
- branch open/close counts;
- explicit frontier gap movement;
- stop reason;
- authority-expanded flag.

Legacy bounces may be recorded with UNKNOWN fields. They must not be
back-filled from guesses.

## Why this is part of the recursive loop

The recursion is now:

    L0 research
      -> durable method event

    method events
      -> FR-META-002 aggregate

    aggregate distributions
      -> FR-META-001 L1 protocol comparison

    candidate method
      -> L2 holdout / perturbation / Goodhart audit

    Council
      -> bounded protocol revision

    revised protocol
      -> more method events

That is the first full data path from research activity back into research
method selection.

## Failure biopsy targets

The recorder makes several future operational failures directly measurable:

- no durable transition after excess calls;
- repeated oversized rehydrate sets;
- branch accumulation without closure;
- high MC spend with no decision movement;
- failures that disappear because biopsy telemetry is missing;
- apparent efficiency caused by low telemetry coverage.

These are hypotheses to test, not labels to assume.

## Authority boundary

This component may record and aggregate explicit method metadata.

It may not:

- inspect private chain-of-thought;
- execute local host actions;
- launch paid compute;
- rerun failed workflows automatically;
- modify operational thresholds;
- merge or delete branches;
- promote memory actions.

## Claim ceiling

**APPEND_ONLY_METHOD_EVIDENCE_INFRASTRUCTURE_ONLY**
