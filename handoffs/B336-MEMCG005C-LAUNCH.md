# Bounce Handoff

> **Bounce ID:** B336
> **Status:** MEMCG-005C EXPLICIT HOSTED LAUNCH

Implementation:
`82515df80b1cde1d9b9732510c3abf1454b2aa91`

Fixture repair:
`57d1c0767f3fd3fbeef8902c78cf6a7bc80b3143`

CI:
`36550984469 = success`

Exact launch commit:
`d50af917577493dc457aa0439a192ab90e5f90a1`

Scientific A/B:
- TWO_STEP: MIGRATE receipt on S, then TOUCH_ONE;
- ATOMIC: migrate then immediate measured touch before any status I/O;
- 23 fresh identities per arm per block;
- 4 blocks;
- 184 first-touch probes.

Next: discover/read exact-head MEMCG-005C run once.

Hosted research only.
No local-PC execution.
