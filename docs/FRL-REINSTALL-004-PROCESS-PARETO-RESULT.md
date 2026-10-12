# FRL-REINSTALL-004 Process Lifecycle Pareto — 2026-10-12

Status: LOCAL 100-PAIR PASS

After artifact projection reached microseconds, the next dominant cost was process lifecycle.

100 paired seeds were executed both as a fresh Python process and through one persistent imported worker. Artifact epoch identity was checked before every request.

| Arm | Median | p95 | Memory |
|---|---:|---:|---:|
| cold process | 50.834 ms | 52.332 ms | 18,856 KiB median peak |
| warm worker | 12.284 ms | 12.715 ms | 18,956 KiB median resident |
| already-running in-process lower bound | 11.387 ms | 12.076 ms | harness-resident |

All 100 paired outputs matched semantically.

Warm worker speedup over cold process: **4.14x**.

The warm worker is only **0.897 ms / 7.88%** above the already-running in-process lower bound. Therefore process lifecycle is effectively removed; the remaining request path is dominated by the useful computation itself.

Cost: about 18 MiB remains resident between requests. This creates the finite-RAM trade-off explored by FRL-REINSTALL-005.
