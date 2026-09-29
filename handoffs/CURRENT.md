# CURRENT

> **Latest bounce:** B356
> **Stage:** MEMCG-005F CONFIRMED / RETROSPECTIVE COMPLETE
> **Turn stop reason:** CHAPTER_CHECKPOINT

## MEMCG-005F

Run:
`36558350433`

Decision:
`SUPPORT_REMOTE_LOW_GATE`

Canonical result:
`docs/MEMCG-005F-RESULT.md`

Confirmed primary gate:

`REMOTE_LOW := startup P, measured S!=P, pre_current_pages<=110`

Confirmatory result:
- LOW: 121/123 Q64 = 98.374%
- HIGH: 65/133 Q64 = 48.872%
- Fisher p: 5.932e-22
- LOW blocks: 31/31, 31/32, 39/40, 20/20
- CPU mismatch: 0
- migration delta: 0 in 256/256
- non-{0,+64} failure: 0

## Retrospective

`docs/RETROSPECTIVE-THROUGH-MEMCG-005F.md`

The current measurement-calibration chapter is complete.

## Accepted current chain

- finite-RAM pressure knee survives;
- effective-live-set interval survives;
- observer contamination identified;
- Q64 / 256 KiB memcg accounting mechanism supported;
- calibrated R64 stock phase supported;
- naive durable/perfect seven-slot observation schemes rejected or rendered inconclusive;
- CPU locality is essential;
- REMOTE_LOW admission gate independently confirmed.

## Next chapter

Return to hosted capacity/eviction testing using:
- candidates created on P;
- only LOW candidates admitted;
- measured insertion on remote S;
- direct Q64 verification of every insertion;
- no K inference from invalid identities.

No successor experiment has been launched yet.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
