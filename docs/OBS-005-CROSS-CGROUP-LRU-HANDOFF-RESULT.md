# OBS-005 — Controlled cross-cgroup LRU handoff result

> **Status:** COMPLETE / MECHANISM CONSTRUCTED
> **Run:** \`36625036954\`
> **Launch commit:** \`8561cd58d54fe7aacc3e6c2b22df283f8cafec37\`

## Frozen scale

- 4 hosted blocks
- 4 identities/block
- 16 total trials
- producer A: 17 pages
- trigger B: 14 pages
- batch capacity: 31
- no adaptive replacement
- no b63 reliability claim

## Frozen aggregate classifier

- CONTROLLED_HANDOFF_PASS: 10
- HANDOFF_NONCANONICAL_TIMING: 1
- NO_HANDOFF_UNCHARGE: 1
- COUNTER_UNKNOWN: 3
- SCRUB_NO_FLUSH: 1

Do not rewrite these frozen classes.

## Derived result

15/16 trials passed the scrubber precondition.

All 15/15 scrub-success trials show producer A \`memory.current\` dropping by exactly 17 pages during the trigger phase.

Counter identity remained available in 12 of those 15.

All 12/12 counter-grounded trials directly show a 17-page uncharge on producer A's page counter.

### Current task at the release

- trigger B / \`frltrig\`: 11/12
- third-party \`provjobd...\`: 1/12

### Timing

- canonical B touch14: 10
- B touch13: 1
- third-party flush in B touch4 window: 1

The third-party case directly demonstrates the same ownership/trigger separation seen naturally in OBS-004.

## Primary construction

For canonical trials:

\`producer17 + trigger14 = batch31\`

At B touch14:

- B current task
- LRU flush nr=31
- folios_put nr=31
- producer A page-counter uncharge=17
- producer A memory.current delta=-17

This is direct controlled evidence for cross-cgroup handoff through a shared per-CPU LRU-add batch.

## Noncanonical timing

### Touch13

One trial has B-triggered release at touch13.

Simplest occupancy explanation:

one external LRU-add entry arrived after scrub preconditioning.

\`17 + 1 + 13 = 31\`

### Third-party trigger

Trial 2:2:

- producer counter known;
- producer current drops -17 during B touch4 window;
- selected page-counter uncharge17 matches producer A;
- current task is \`provjobd...\`;
- stack is LRU/folio-batch.

The runner itself preempted B and flushed A's dead folios.

This is informative contamination, not a mechanism contradiction.

## Receipt-limited block 3

Three trials have raw canonical B-touch14 -17 but no retained producer pc_try receipt.

The block-3 trace workload was large enough to overwrite earlier ring-buffer records.

They remain COUNTER_UNKNOWN in the frozen result.

## Evidence

Raw manifest:
- files: 96
- bytes: 150,274,057
- content-set SHA-256:
  \`dfbf406339e955779333346f935a6312f7e45a7d06c57ce14378bcd38ca355e0\`

Aggregate ZIP:
- SHA-256:
  \`83069827e759bb3060d9f3e8a71cda6e73d24ae15b7fd4acc9ad6f9e3edbb989\`

Drive COLD:
\`Catfood Lab Evidence/finite-ram-lab/OBS-005-CROSS-CGROUP-LRU-HANDOFF-v1/run-36625036954\`

Verification:
\`5 / 5 BYTE-IDENTICAL PASS\`

## Conclusion

The -17 contaminant is a shared-batch ownership/trigger phenomenon.

A task does not need to own the released folios to trigger their accounting transition.

The Q64 lane can now move from caller forensics to an observer that separates charge and release emissions.
