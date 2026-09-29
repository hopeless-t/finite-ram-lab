# B388 — Rare specimen census

Objective: reconstruct one row per historical trial identity across G-A, G-F, G0 Stage A, and controlled-spawn v2.

Inputs: Actions runs 36563233676, 36577573774, 36591417373, 36595481746 and their result documents. All raw artifacts were downloaded for read-only analysis. No experiment was launched.

Completed: `analysis/rare_specimens.py`, `analysis/inputs/RARE-SPECIMEN-CENSUS-v1.csv`, and `docs/RARE-SPECIMEN-CENSUS-v1.md`. The table contains 4,680 unique identities; valid LOW exact-zero counts are G-A 28, G-F 91, G0 19. Historical missing PTE data and different spawn endpoint semantics are explicit.

Next: fit the ordered model ladder with block-aware validation, retain natural and constructed processes separately, and record confirmed/supported/unresolved/rejected claims in MATH-014. Authority is retrospective analysis only.
