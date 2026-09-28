# CURRENT

> **Latest bounce:** B221
> **Stage:** REC-003 / MONTE CARLO CORRUPTION + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Hardening implemented

- lifecycle fail-close: one file = one run, contiguous seq, terminal run_end;
- clean incomplete crash logs remain forensic/incomplete;
- malformed partial JSON rolls back;
- raw evidence path ownership uses exclusive create;
- incomplete projection can later be completed from a full raw stream.

## Monte Carlo campaign

Commit:

`a2f49a1865655d7ec79d95525d58df7e3f06053c`

12 corruption families are sampled in one-to-four mutation combinations, with valid controls and a relaxed negative-control validator.

Unit CI uses deterministic 5,000-world campaigns. A separate 100,000-world hosted campaign remains unlaunched.

## Hosted validation

Ordinary CI run:

`36427033616`

Last and only read in B221:

`in_progress`

Do not poll again in the same bounce.

## Next fresh-bounce action

Read `36427033616` once.

- success -> launch the dedicated 100,000-world REC-003 campaign in a separate commit;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> preserve and fix the discovered counterexample before any launch.

Then attack physical write/flush/partial-write corruption.

REC-002 remains un-relaunched.
STRATA-005 remains frozen and unlaunched.

## Authority boundary

Repository/hosted synthetic validation only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
