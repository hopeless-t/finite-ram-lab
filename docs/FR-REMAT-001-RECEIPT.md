# FR-REMAT-001 — Retain / Recompute / Offload Receipt

Status: **PASS / SYNTHETIC REMATERIALIZATION PLANNER VALIDATED**

## Qualification

- workflow run: 37120307862
- job: 111194965257
- execution head: 6c7d7ed3fbe7c67680aa5b8588ba011441c14bba
- artifact ID: 11273267119
- artifact ZIP SHA256: 6522c85970afe02b3a000871b25bb531ff4d7ab288fbfa1df07420a0e5605d05
- spec SHA256: 249205c242f799435adfa77a3b58cbde643cccae464a33a5ed4baf329eb73ee8
- result SHA256: bb93264757a7c1d0f8496146eaf6b9ee68db7301d7957962abe4ffa0014424e7

## Frozen result

- total synthetic state: 648 MiB
- fast budget: 256 MiB
- slow budget: 256 MiB
- KEEP_ALL: infeasible
- DROP_LARGEST_RECOMPUTE objective: 116.375
- CHEAP_RECOMPUTE_FIRST objective: 60.5625
- optimal mixed objective: 51.2045

Optimal mixed policy:

- POINTWISE_A -> RECOMPUTE
- MATMUL_B -> OFFLOAD
- ATTN_C -> KEEP
- NORM_D -> RECOMPUTE
- EMBED_E -> RECOMPUTE
- ROUTER_F -> KEEP
- EXTERNAL_RESULT_G -> OFFLOAD

Result:

- fast residency: 240 MiB
- slow residency: 200 MiB
- mean overhead proxy: 40 ms
- tail proxy: 65.95 ms
- transfer: 656 MiB

## Safety invariant

Non-rebuildable state is never eligible for RECOMPUTE.

## Claim ceiling

**SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY**
