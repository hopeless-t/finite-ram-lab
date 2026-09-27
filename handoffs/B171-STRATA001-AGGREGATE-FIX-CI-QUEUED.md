# Bounce Handoff

> **Bounce ID:** B171
> **Status:** COMPLETE / STRATA-001 PILOT AGGREGATE FIX CI QUEUED / TURN CLOSED
> **Turn stop reason:** EXTERNAL_WAIT

## Fix commit

`71612c6b37dcfe5a9d332f5c8d0f9d1ed444d280`

## External run observed exactly once

- run: `36337262716`
- workflow: `CI`
- status: `queued`
- conclusion: not yet available
- attempt: `1`

No repeated polling was performed.

## Preserved pilot evidence

Pilot run `36336994450`:

- all six experimental block jobs: SUCCESS
- aggregate job only: FAILURE

The six block artifacts remain the source of physical pilot evidence.

The failure was a collector path-name mismatch, not a trial failure.

## Next fresh-turn action

1. rehydrate B171;
2. read CI run `36337262716` exactly once;
3. SUCCESS → download/recover the six existing block artifacts and aggregate with the fixed collector;
4. pending → checkpoint EXTERNAL_WAIT again;
5. failure → inspect only the failing job.

Do not re-run the 36 physical trials unless recovery proves impossible.

## Interesting standing findings

1. STRATA-001 capability PASS showed MMAP and buffered pread taking cold files from 0% to 100% page-cache residency while O_DIRECT remained at 0% on the selected ext4 runner.
2. The full 36-trial pilot physically executed successfully across all six runner blocks; only post-processing failed.
3. LABEL-001 exploratory intake found the assignment-derived misalignment proxy agreed with observed natural residency state in about 88% of NO_HINT trials, indicating it is useful but not identical to the actual memory state.

## Attribution

STRATA-001 remains explicitly inspired by Niko1221/Strata.

No upstream source code is copied.

## Authority boundary

Pilot recovery only.
