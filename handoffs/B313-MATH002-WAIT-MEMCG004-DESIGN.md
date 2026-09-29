# Bounce Handoff

> **Bounce ID:** B313
> **Status:** MATH-002 RUNNING / MEMCG-004 CALIBRATION DESIGN FROZEN

MEMCG-003B primary is frozen:
`REJECT_K7_SLOT_MODEL_B`

Key result:
- no passive >=16-page target drop through eight distinct challengers in 4/4 blocks;
- final +64 recharge in 3/4 distinct blocks;
- passive-drop proxy is incomplete.

MATH-002 secondary run:
`36529563011`

Single status read:
`in_progress`

No second read was performed.

Source inspection shows worker creation does not imply a known stock state:
- stock entry disappears at zero;
- refunds can refill or drain entries;
- kmem/socket uncharges can feed the same stock.

MEMCG-004 frozen:
directly calibrate a 63-page stock state by stopping at an observed +64 charge, hold it passively, then verify the next +64 occurs on the 64th subsequent one-page touch.

Next fresh bounce:
read MATH-002 run once; then implement MEMCG-004.

Hosted research only.
