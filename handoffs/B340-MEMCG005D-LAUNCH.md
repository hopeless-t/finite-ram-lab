# Bounce Handoff

> **Bounce ID:** B340
> **Status:** MEMCG-005D EXPLICIT HOSTED LAUNCH

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

CI:
`36552457074 = success`

Exact launch commit:
`f4ca08442547142f1aaf0d0113f0653da3d7ee09`

Scientific A/B:
- SELF_ATOMIC: worker self-migrates then immediate touch;
- EXTERNAL_ATOMIC: controller externally migrates PID, confirms S, samples mid current, then shared GO triggers immediate touch;
- 23 identities per arm per block;
- 4 blocks;
- 184 probes total.

Next: discover/read exact-head MEMCG-005D run once.

Hosted research only.
No local-PC execution.
