# CURRENT

> Latest bounce: B397
> Stage: -17 MECHANISM CONSTRUCTED / CROSS-CGROUP LRU HANDOFF PROVEN
> Stop: READY FOR OBS-006 DECONTAMINATED CHARGE-SIDE Q64 OBSERVER

## OBS-005

Run:
\`36625036954 = success\`

Frozen classifier:
- CONTROLLED_HANDOFF_PASS 10
- HANDOFF_NONCANONICAL_TIMING 1
- NO_HANDOFF_UNCHARGE 1
- COUNTER_UNKNOWN 3
- SCRUB_NO_FLUSH 1

Derived:
- scrub precondition success 15/16
- producer memory.current exact -17 during trigger phase 15/15
- producer counter receipt retained 12
- producer page-counter uncharge17 12/12
- current task B/frltrig 11
- current task third-party provjobd 1

Canonical:
\`producer17 + trigger14 = batch31\`

At B touch14:
\`flush31 -> folios_put31 -> producer counter uncharge17 -> producer current -17\`

## Mechanism

The recurrent -17 contaminant is:

deferred owner-A dead folios
+ shared per-CPU LRU-add batch
+ flush by any task on that CPU
-> owner-A page-counter uncharge17

Owner, staging scope, trigger actor, and accounting recipient are distinct.

## Q64 implication

memory.current is a net emission, not a direct stock-state read.

A measured touch may combine:
- data charge / stock refill
- LRU release
- stock drain
- PTE charge
- other asynchronous accounting

The -17 lane is sufficiently closed.

## Evidence

Raw:
- files 96
- bytes 150,274,057
- SHA:
  \`dfbf406339e955779333346f935a6312f7e45a7d06c57ce14378bcd38ca355e0\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-005-CROSS-CGROUP-LRU-HANDOFF-v1/run-36625036954\`

Verification:
\`5/5 BYTE-IDENTICAL PASS\`

## Next

OBS-006 decontaminated charge-side Q64 observer.

Primary task:
identify memcg batch refill/charge directly even when net memory.current delta is masked by an unrelated release.

Do not restart b63 reliability scaling until OBS-006 is validated.

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
