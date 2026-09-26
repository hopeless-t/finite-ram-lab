# HYP-003 Implementation Notes

> **Status:** IMPLEMENTED / NOT YET LAUNCHED

The implementation follows the frozen shared-VMA 2×2×2 factorial.

Key fail-closed property:

> future HOT identity is not used by the workload until after the post-burst residency snapshot.

Implemented artifacts:

- src/finite_ram_lab/hyp003_workload.py
- src/finite_ram_lab/hyp003_study.py
- tests/test_hyp003.py

The study records:

- direct aligned-vs-misaligned HOT residency;
- the CHAR-002 fault-order manipulation check;
- aligned-vs-misaligned reuse latency;
- swap/refault/fault diagnostics;
- content integrity and OOM state.

No scientific run is authorized by implementation alone.
