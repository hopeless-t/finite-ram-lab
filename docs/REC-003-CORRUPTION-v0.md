# REC-003 Evidence Corruption Campaign v0

> **Status:** STARTED / FAILURE-INJECTION REGRESSIONS ADDED
> **Authority:** REPOSITORY VALIDATION ONLY

## Objective

Try to make REC-001 accept structurally corrupted evidence without producing an explicit failure.

The governing requirement is not "the recorder never fails." It is:

> corrupted or ambiguous evidence must not silently become a valid completed run.

## First attack family: JSONL lifecycle corruption

Adversarial review of the original ingester found that per-record validation alone was insufficient.

The old ingestion path did not explicitly enforce the file-level lifecycle:

- one JSONL file corresponds to one run;
- the first record is `run_start` with seq 0;
- sequence numbers are contiguous;
- `run_end` is terminal.

Therefore crafted evidence could attempt:

1. append a sample after `run_end`;
2. append a second `run_end`;
3. remove a middle record and leave a sequence gap;
4. splice a different `run_id` into the same file.

These are now explicit fail-closed conditions.

## Crash semantics

A file that ends cleanly at a complete JSON line but lacks `run_end` is not rejected.

It is retained as an incomplete forensic run:

- records are queryable;
- `runs.status` remains NULL;
- it cannot silently masquerade as a completed PASS.

A malformed partial JSON tail remains a hard ingestion failure with transaction rollback.

## Regression set

REC-003 v0 adds tests for:

- record after run_end -> reject + rollback;
- second run_end -> reject + rollback;
- sequence gap -> reject + rollback;
- mixed run_id -> reject + rollback;
- clean incomplete crash log -> ingest as incomplete;
- existing malformed tail / duplicate conflict / rebuild tests remain active.

## Next attack families

After ordinary CI is green:

- same-file concurrent writers / create race;
- disk/write failure injection;
- SQLite corruption and rebuild behavior;
- extreme record size / special-character payloads;
- high-frequency recording and observer-effect transition.

No hosted pressure experiment is launched by REC-003 itself.
