# Bounce Handoff

> **Bounce ID:** B337
> **Status:** EXTERNAL_WAIT / MEMCG-005C HOSTED RUN IN PROGRESS

Exact launch commit:
`d50af917577493dc457aa0439a192ab90e5f90a1`

Scientific run:
`36551226475`

Single B337 status read:
`in_progress`

No second read was performed.

Scientific A/B:
- TWO_STEP: MIGRATE receipt on S, then TOUCH_ONE;
- ATOMIC: migrate then immediate measured page touch before any status I/O;
- 23 fresh identities per arm per block;
- 4 blocks;
- 184 probes total.

Primary question:
does ATOMIC materially reduce non-Q64 first-touch failures relative to TWO_STEP?

Next fresh bounce:
- read run `36551226475` exactly once;
- success -> fetch aggregate once and canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
