# CURRENT

> **Latest bounce:** B318
> **Stage:** MEMCG-004 PASS / CALIBRATED STOCK ESTABLISHED
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## MEMCG-004 canonical result

Run:
`36541998246`

Decision:
`SUPPORT_CALIBRATED_STOCK`

CALIBRATED:
- fresh +64 calibration observed in 4/4 blocks;
- calibration touch indices [2,5,5,4];
- passive hold stable in 4/4;
- next +64 charge at validation touch 64 in 4/4.

NO_HOLD:
- R=64 in 4/4.

CONTROL_NO_PRIME:
- R=[5,5,3,4].

Model:
- unique best R=64;
- absolute error 0;
- 21-bit description advantage over arbitrary event locations.

Canonical result:
`docs/MEMCG-004-RESULT.md`

## Accepted mechanism-level advance

Worker existence is not a known stock state.

An observed fresh +64 batch followed by immediate stop **is** a reproducible calibration point.

The subsequent 63 no-charge touches plus fresh charge on touch64 are exactly source-consistent with 63 cached pages.

## MATH-002

Prior pmndrs/math sidecar remains:
`INFRA_FAILURE / NO_SCIENTIFIC_RESULT`

It does not affect MEMCG-004.

## Next fresh-bounce action

Freeze MEMCG-005 as a calibrated seven-slot capacity experiment.

Prefer a one-shot replica design if testing target state after each challenger would mutate the state being measured.

Do not launch during design.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
