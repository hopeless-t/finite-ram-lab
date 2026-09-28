# Bounce Handoff

> **Bounce ID:** B218
> **Status:** EXTERNAL_WAIT / REC-003 LIFECYCLE HARDENING CI IN PROGRESS

## B217

Commit:

`8a5875790610eacc7b8cc7e72ef9184d3975b690`

Changes:

- corrected the REC-002 CR/LF regression assertions by rewriting the test block;
- added REC-003 lifecycle corruption regressions;
- hardened the ingester to enforce one-run-per-file, contiguous seq, and terminal run_end;
- preserved clean incomplete crash logs as forensic incomplete runs.

## CI

Ordinary CI run:

`36425701676`

Single status read in B218:

`in_progress`

No second read was performed.

## Next fresh-bounce action

Read `36425701676` exactly once.

- success -> accept REC-003 lifecycle hardening and continue to the next bounded corruption family;
- pending -> retain EXTERNAL_WAIT;
- failure -> inspect the failing invariant only; no blind retry.

REC-002 relaunch remains separate and unperformed.

## Authority boundary

Repository/hosted validation only. No local-PC execution. No STRATA-005 launch. No memory-control policy authorized.
