# B362 — MEMCG-005G-B implemented

Frozen CAP8 vs CAP70 footprint control is implemented.

Implementation:
- specs/MEMCG-005G-B-BIOPSY-FOOTPRINT-CONTROL-v1.json
- src/finite_ram_lab/memcg005gb_footprint_control.py
- .github/workflows/memcg-005g-b-footprint-control.yml
- tests/test_memcg005gb_footprint_control.py

Design invariants:
- 16 independent hosted blocks
- 64 candidates/block
- CAP8/CAP70 alternating; parity reversed by block
- identical first-touch path
- no biopsy in primary A/B
- Fisher two-sided primary
- Mantel-Haenszel OR + block heterogeneity secondary

No launch marker exists.

Next: discover/read ordinary CI once.
