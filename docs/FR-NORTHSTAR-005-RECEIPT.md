# FR-NORTHSTAR-005 Receipt

Status: **PASS / FIRST COMPLETE NORTH-STAR GAP-CLOSURE LOOP VALIDATED**

- workflow run: 37124206203
- job: 111206123662
- execution head: 703bf059921e96497d9732cd935fda981fe28fce
- artifact ID: 11273713886
- artifact ZIP SHA256: bf1f984a0884fc73126ca415a686b44af495639dbb33279efc0b88e3de46cd4f
- spec SHA256: 2873ed33b6714725ee0ae6ce6438b061d777398248f49760155f2c17d4eee451
- result SHA256: f5e2f1a1f042ad61f8473dee21221546f63fb544d06d0c9b08ffb0a09b994714

Frozen lifecycle:

- before FR-XFER-001: CAPABILITY_GAP
- after transfer primitive registration: MODEL_GAP
- after transfer effect model: FRONTIER_REACHED

Transfer-bound fixture:

- current resident: 560 MiB
- budget: 600 MiB
- staged-copy peak: 624.0078125 MiB -> over budget
- direct no-staging peak: 592.00390625 MiB -> fits
- shared-view peak: 560 MiB -> fits if semantics allow

Research policy:

- open new transfer-mechanism lane: false
- move to host-bound qualification only if a real workload needs the primitive
- otherwise return to the global gap selector

Live actions executed: 0.

Claim ceiling:

**HOSTED_PROXY_NORTH_STAR_LOOP_CLOSURE_ONLY**
