# CURRENT

> **Latest bounce:** B218
> **Stage:** REC-003 / LIFECYCLE HARDENING + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Break/fix completed in B217

### REC-002 harness

The CR/LF regression test was rewritten to inspect actual control bytes.

### REC-003 lifecycle corruption

The ingester now rejects atomically:

- records after run_end;
- a second run_end;
- sequence gaps;
- mixed run IDs in one JSONL file.

It requires:

- one file = one run;
- first record = run_start seq 0;
- contiguous seq;
- run_end is terminal.

A clean crash-truncated stream without run_end remains queryable as an incomplete run with NULL status.

Malformed partial JSON remains a hard rollback failure.

## Validation

B217 commit:

`8a5875790610eacc7b8cc7e72ef9184d3975b690`

Ordinary CI:

`36425701676`

Last and only read in B218:

`in_progress`

Do not poll again in the same bounce.

## Next fresh-bounce action

Read CI run `36425701676` once.

- success -> accept this corruption-hardening tranche and attack the next REC-003 family;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect failure only and repair the violated invariant.

REC-002 relaunch remains separate.

STRATA-005 remains frozen and unlaunched.

## Authority boundary

Repository/hosted validation only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
