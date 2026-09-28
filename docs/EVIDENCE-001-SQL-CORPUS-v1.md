# EVIDENCE-001 Queryable SQL Corpus Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Goal

Turn accepted finite-ram-lab evidence into a queryable SQLite corpus for hypothesis discovery and counterexample search.

The corpus is not a new authority source and must not replace raw evidence.

It is a derived research index over canonical accepted results.

## Included canonical studies

v1 seeds:

- STRATA-004
- STRATA-005
- STRATA-006
- STRATA-007
- STRATA-008
- STRATA-009
- REC-003
- REC-004

## Core rule

Measurement semantics must be explicit.

The corpus must distinguish:

- `clean_pre_observer`
- `legacy_post_observer`
- `post_observer_diagnostic`
- `not_applicable`

No SQL query may silently treat legacy post-observer floor as a clean workload floor.

## Schema

### experiments

One row per canonical experiment.

Fields include:

- experiment_id
- run_id
- result_doc
- status
- runner
- artifact_digest
- accepted_at_bounce
- inference_boundary

### response_cells

One row per aggregate response-surface cell.

Dimensions:

- experiment_id
- condition_id
- runner
- memory_high_mib
- memory_max_mib
- hot_anon_mib
- cold_file_mib
- release_interval_mib
- arm_kind

Outcomes:

- median_high_events
- positive_trials
- trial_count
- median_peak_mib
- median_floor_mib
- floor_semantics
- median_file_residency
- advice_calls
- oom_any

### onset_intervals

One row per accepted onset interval.

Fields:

- experiment_id
- condition_id
- memory_high_mib
- hot_anon_mib
- cold_file_mib
- knee_lower_exclusive_mib
- knee_upper_inclusive_mib
- right_censored
- transformed_lower_exclusive_mib
- transformed_upper_inclusive_mib

### measurement_notes

Machine-readable semantic corrections and caveats.

Examples:

- STRATA-007/008/009 fine floor is legacy post-observer;
- REC-003 detects observer-size effect;
- REC-004 adopts pre-observer floor prospectively.

## Required SQL views

### v_live_set_transform

Expose onset intervals with:

`knee + hot`

for live-set invariance checks.

### v_capacity_knee

Expose 96 / 192 / 384 MiB capacity series at H=160, hot=64.

### v_clean_floor

Only rows whose `floor_semantics = clean_pre_observer`.

### v_legacy_floor

Legacy post-observer rows, explicitly separated.

### v_counterexamples

Rows that violate a supplied candidate invariant or fall outside its tested envelope.

v1 can implement concrete checks for:

- fixed raw knee across pressure settings;
- `K+hot` interval compatibility across STRATA-006;
- cold-capacity knee invariance across STRATA-007/008/009.

## Frozen discovery queries

The hosted corpus run must emit results for:

1. pressure-axis fixed-knee intersection;
2. live-set transformed interval intersection;
3. capacity-axis knee equality;
4. clean-floor span from REC-004;
5. observer contamination evidence from REC-003/004;
6. candidate next-axis ranking based on untested dimensions.

## Data-quality rules

- every seed row names its canonical source document;
- every experiment carries run ID and artifact digest when available;
- derived rows must be deterministic;
- duplicate primary keys fail the build;
- unknown floor semantics fail validation;
- no raw evidence is rewritten.

## Output

Hosted EVIDENCE-001 run produces:

- `corpus.sqlite`
- `query-results.json`
- `query-results.md`
- `schema.sql`
- normalized seed JSON

## Pseudo-Council

- **Measurement:** semantic typing prevents contaminated metrics from silently re-entering clean analysis.
- **Statistics:** SQL finds patterns and counterexamples; it does not create causal proof.
- **Systems:** keep the corpus deterministic and rebuildable from committed seed data.
- **Research:** use queries to rank high-information next experiments.
- **Authority:** corpus output is proposal/evidence synthesis only.

Consensus:

**freeze EVIDENCE-001 as a rebuildable SQLite evidence corpus and hypothesis-discovery surface.**

## Launch boundary

Design only.
Implementation and hosted corpus build are separate bounces.
No local-PC execution.
