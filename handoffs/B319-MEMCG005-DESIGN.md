# Bounce Handoff

> **Bounce ID:** B319
> **Status:** COMPLETE / MEMCG-005 CALIBRATED K7 DESIGN FROZEN

MEMCG-004 established a reproducible calibrated stock primitive:
- +64 calibration
- 63 silent consumptions
- next +64 exactly on touch64
- 4/4 blocks

MEMCG-005 upgrades seven-slot testing by normalizing every prestarted worker to a known EMPTY phase before measured insertion.

Per independent replica:
- prestart W0..W6 + T + C1..C8
- normalize all 16 to EMPTY:
  fresh +64 then exactly 63 consumptions
- measured insert W0..W6, each requiring +64
- measured insert T, requiring +64
- measured insert C1..Cm, each requiring +64
- one-shot target probe

Tested m:
`{0,5,6,7,8}`

Source prediction:
- m=0,5,6 -> target PRESENT
- m=7,8 -> target ABSENT

4 blocks × 5 independent replicas = 20 replicas.

Next: implement only. Do not launch during implementation bounce.

Hosted research only.
