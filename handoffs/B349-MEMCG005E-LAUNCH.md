# Bounce Handoff

> **Bounce ID:** B349
> **Status:** MEMCG-005E EXPLICIT HOSTED LAUNCH

Implementation:
`4931eea15e96b3d9ba2e961ae5e9a887921a4ad5`

CI:
`36555769313 = success`

Exact launch commit:
`421adf66d76df37d2a00a743f775ba26ef2bb16e`

Prospective threshold:
`LOW iff pre_current_pages <= 110`

Arms:
- LOCAL_P
- REMOTE_S

Scale:
32 identities per arm per block, 4 blocks, 256 probes.

Next: discover/read exact-head MEMCG-005E run once.

Hosted research only.
No local-PC execution.
