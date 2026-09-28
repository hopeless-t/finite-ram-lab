# CURRENT

> **Latest bounce:** B273
> **Stage:** EVIDENCE-001 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## SQL corpus implementation

Files:

- `evidence/EVIDENCE-001/seed-v1.json`
- `sql/evidence001_schema.sql`
- `src/finite_ram_lab/evidence001_sql_corpus.py`
- `.github/workflows/evidence-001-sql-corpus.yml`
- `tests/test_evidence001_sql_corpus.py`

Seeded canonical experiments:
- STRATA-004..009
- REC-003..004

Semantic protection:
- clean_pre_observer
- legacy_post_observer
- post_observer_diagnostic
- not_applicable

Discovery output tests:
- fixed raw knee contradiction across pressure
- live-set transformed interval intersection
- cold-capacity knee invariance
- clean-floor span
- observer-effect rows
- next untested-axis ranking

No launch marker exists.

## Next fresh-bounce action

Discover/read B273 ordinary CI exactly once.

- success -> explicit EVIDENCE-001 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
