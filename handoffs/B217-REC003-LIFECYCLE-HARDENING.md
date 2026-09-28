# Bounce Handoff

> **Bounce ID:** B217
> **Status:** COMPLETE / REC-003 LIFECYCLE CORRUPTION HARDENING / CI PENDING

## What broke

Two independent defects are now addressed in one bounded repository validation step.

### REC-002 test escape defect

B215 CI run `36423465750` failed because the source still contained literal two-character byte sequences `b"\\r"` and `b"\\n"`.

The REC-002 regression file has been rewritten so it checks actual control bytes.

### REC-001 ingestion lifecycle gap

Adversarial REC-003 review found that the ingester validated individual records but did not fully validate the JSONL stream lifecycle.

Old behavior could admit crafted structures such as a record after run_end, a second run_end, a sequence gap, or mixed run IDs unless another constraint happened to catch them.

## Fix

The ingester now enforces:

- first record = run_start seq 0;
- exactly one run_id per JSONL file;
- contiguous sequence numbers;
- run_end is terminal.

A clean crash-truncated stream with no run_end remains ingestible as incomplete evidence; status remains NULL.

Malformed JSON tails remain atomic failures.

## Next action

Read ordinary CI for B217 exactly once.

If successful, accept REC-003 lifecycle hardening, then decide between:

1. REC-002 relaunch; and
2. the next REC-003 corruption family.

Do not infer either execution from this commit.

## Authority boundary

Repository/hosted validation only. No local-PC execution. No STRATA-005 launch. No memory-control policy authorized.
