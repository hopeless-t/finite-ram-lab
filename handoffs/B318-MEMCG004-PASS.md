# Bounce Handoff

> **Bounce ID:** B318
> **Status:** COMPLETE / MEMCG-004 SUPPORT_CALIBRATED_STOCK

Run:
`36541998246`

Decision:
`SUPPORT_CALIBRATED_STOCK`

CALIBRATED:
- calibration touch = [2,5,5,4]
- calibration jump = +64 pages in 4/4
- passive hold max drop = 0 in 4/4
- validation R = [64,64,64,64]

NO_HOLD:
- calibration touch = [2,6,7,3]
- validation R = [64,64,64,64]

CONTROL_NO_PRIME:
- R = [5,5,3,4]

Model:
- best R = 64
- total absolute error = 0
- fixed-R64 code = 7 bits
- arbitrary locations = 28 bits

Interpretation:
conditioning on an observed fresh Q64 charge creates a reproducible source-consistent 63-page residual stock state.

Next:
freeze MEMCG-005 calibrated seven-slot design.

Hosted research only.
No local-PC execution.
