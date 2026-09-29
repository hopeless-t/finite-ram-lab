# B397 — Controlled cross-cgroup LRU handoff constructed

## Status

OBS-005 COMPLETE / MECHANISM CONSTRUCTED / EVIDENCE COLD-VERIFIED.

Run:
\`36625036954\`

## Frozen classifier

16 trials:

- CONTROLLED_HANDOFF_PASS: 10
- HANDOFF_NONCANONICAL_TIMING: 1
- NO_HANDOFF_UNCHARGE: 1
- COUNTER_UNKNOWN: 3
- SCRUB_NO_FLUSH: 1

Keep these classes unchanged.

## Derived mechanism view

Scrub precondition succeeded:
15/16

Among those 15:

- 15/15 show producer A memory.current exact -17 during trigger phase.

Counter identity receipt survived:
12/15

Among those 12:

- 12/12 show page_counter_uncharge(...,17) on producer A's page-counter pointer.

Current task at release:

- trigger B / frltrig: 11
- third-party provjobd: 1

B-triggered timing:

- touch14: 10
- touch13: 1

Third-party case:
- A counter known
- current task provjobd
- LRU/folio-batch stack
- A memory.current -17

Thus another task can flush dead folios owned by A from the shared per-CPU LRU-add batch.

## Mechanism

For canonical trials:

\`A17 + B14 = 31\`

B touch14:

\`LRU flush31 -> folios_put31 -> A page-counter uncharge17 -> A memory.current -17\`

The transition roles are distinct:

1. logical owner: producer A
2. physical staging: per-CPU LRU-add batch
3. transition trigger: B or another task on the CPU
4. accounting target: A page counter

## Receipt-loss caveat

Three block-3 trials have canonical raw touch14 -17 but no retained producer pc_try receipt.

Block 3 trace profile is extremely large and older pc_try events were overwritten.

They remain COUNTER_UNKNOWN in the frozen result.

## Evidence

Raw:
- 96 files
- 150,274,057 bytes
- content-set SHA:
  \`dfbf406339e955779333346f935a6312f7e45a7d06c57ce14378bcd38ca355e0\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-005-CROSS-CGROUP-LRU-HANDOFF-v1/run-36625036954\`

Verification:
\`5/5 BYTE-IDENTICAL PASS\`

## Documents

- docs/OBS-005-CROSS-CGROUP-LRU-HANDOFF-RESULT.md
- docs/MATH-016-SHARED-LRU-HANDOFF.md
- analysis/inputs/OBS-005-DERIVED-SUMMARY-v1.json
- evidence/OBS-005/COLD-REPLICA-v1.json

## Research transition

The -17 forensic lane is sufficiently closed for the Q64 mainline.

Do not spend the next bounce on additional caller hunting.

Next:
OBS-006 decontaminated charge-side Q64 observer.

Goal:
separate charge/reset emissions from unrelated release emissions so that a Q64 refill can be identified even when
net memory.current is masked by LRU release, stock drain, or other asynchronous accounting.

No b63 reliability scaling until OBS-006 is validated.
