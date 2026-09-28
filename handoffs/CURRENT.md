# CURRENT

> **Latest bounce:** B274
> **Stage:** EVIDENCE-001 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Scientific state

Accepted finite-RAM relation:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval + bounded overhead`

for the tested one-shot Linux streaming workload.

Capacity series 96 / 192 / 384 MiB shares:

`80 < K <= 88 MiB`

REC-004 adopts pre-observer workload-floor measurement prospectively.

## EVIDENCE-001

Exact implementation:

`8397f32fb67325cc081783435088f5d60334c051`

Corpus includes canonical:
- STRATA-004..009
- REC-003..004

SQLite semantics explicitly separate:
- clean_pre_observer
- legacy_post_observer
- post_observer_diagnostic
- not_applicable

Hosted build will emit:
- corpus.sqlite
- query-results.json
- query-results.md

No launch marker exists.

## CI

Run:

`36445229520`

Single B274 read:

`queued`

Do not poll again in this bounce.

## Next fresh-bounce action

Read `36445229520` exactly once.

- success -> explicit EVIDENCE-001 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
