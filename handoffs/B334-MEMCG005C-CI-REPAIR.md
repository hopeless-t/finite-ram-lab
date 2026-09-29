# Bounce Handoff

> **Bounce ID:** B334
> **Status:** MEMCG-005C CI FAILURE REPAIRED

Original implementation:
`82515df80b1cde1d9b9732510c3abf1454b2aa91`

Failed CI:
`36550320654`

Exposed invariant:
`tests/test_memcg005c_atomic_first_touch.py::test_support`

Root cause:
synthetic fixture inverted the meaning of "fail".

For `atomic_fail=1`, the fixture created 91 failures and 1 success.

Repair commit:
`57d1c0767f3fd3fbeef8902c78cf6a7bc80b3143`

Only the synthetic fixture predicate changed:
- before: `global_i >= 92-fail`
- after: `global_i < 92-fail`

Scientific analyzer, worker, workflow, and preregistered thresholds are unchanged.

Next:
read repair CI exactly once.

Hosted research only.
No local-PC execution.
