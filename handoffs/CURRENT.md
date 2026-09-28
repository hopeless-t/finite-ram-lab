# CURRENT

> **Latest bounce:** B217
> **Stage:** REC-003 / LIFECYCLE CORRUPTION HARDENED / CI PENDING

## REC-002 status

The first REC-002 hosted run remains invalid with zero valid trials.

The CRLF producer bug is fixed, and the byte-level regression test has now been rewritten to inspect actual CR/LF control bytes.

No REC-002 relaunch has been authorized by this commit.

## REC-003 first corruption family

JSONL stream lifecycle is now fail-closed for:

- record after run_end;
- second run_end;
- sequence gap;
- mixed run IDs.

The stream contract is:

- one file = one run;
- first record = run_start seq 0;
- seq is contiguous;
- run_end is terminal.

Clean incomplete crash logs remain ingestible for forensic analysis with NULL run status.

Malformed partial JSON remains rejected atomically.

See `docs/REC-003-CORRUPTION-v0.md`.

## Next action

Read B217 ordinary CI exactly once.

- success -> accept lifecycle hardening and continue bounded break/fix work or separately relaunch REC-002;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect failure only; no blind retry.

## Parent research state

REC-001 v0 remains the evidence substrate under hardening.

STRATA-005 remains frozen and unlaunched.

## Authority boundary

Repository/hosted validation only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
