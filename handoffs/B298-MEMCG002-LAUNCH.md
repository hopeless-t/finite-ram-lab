# Bounce Handoff

> **Bounce ID:** B298
> **Status:** MEMCG-002 EXPLICIT HOSTED LAUNCH

Repair commit:
`3e563db223c80938a09a8a1567c8b9fe4e5836d4`

Repair CI:
`36455336164 = success`

Exact launch commit:
`f359c7f619e4916aef403c33156307862204395a`

Causal arms:
- FIXED_TOUCH
- MIGRATE_TOUCH A->B after step128
- ROUNDTRIP_TOUCH A->B after128, B->A after192
- ROUNDTRIP_CONTROL

4 blocks / 16 trials.

Next: discover/read exact-head MEMCG-002 run once.

Hosted research only.
No local-PC execution.
No memory-control policy.
