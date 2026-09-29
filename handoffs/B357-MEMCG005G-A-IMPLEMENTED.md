# B357 — MEMCG-005G-A frozen and implemented

Goal:
independently test the fixed EARLY 0..7 vs STEADY 8..31 REMOTE_LOW failure concentration.

Design:
- 24 independent hosted block jobs
- 32 fresh identities/block
- threshold <=110 pages frozen
- primary one-sided Fisher EARLY failure > STEADY
- two-rate vs shared-rate Bayes factor secondary
- first-touch zero LOW failures receive residual-stock biopsy through touch65
- unchanged MEMCG-005D worker, pre-mapped 70 pages
- no K7 inference

No launch marker exists.

Next: read ordinary CI exactly once.
