# FR-META-008 Receipt

Status: **PASS / MATCHED-MONTE-CARLO FIXTURE REUSE VALIDATED**

- workflow run: 37137262888
- job: 111244211919
- execution head: e6c11376af5be28b7e6ecfdbe7ee0147b45962cd
- qualification artifact ID: 11279345464
- artifact ZIP SHA256: aa12e1febafb10ead7e8cbca000b5c32e45edfb77bbb571debc428b8f1ab6066

Scientific work unchanged:

- MC episodes per panel: 200,000
- matched random tape: unchanged
- analytic comparison: unchanged
- utility thresholds: unchanged
- run_panel implementation: unchanged

Test-harness work:

- baseline run_panel calls in class: 3
- candidate calls: 1
- baseline MC episode evaluations: 600,000
- candidate: 200,000
- structural duplicate-work reduction: 66.67%

Observed CI timing:

- pre-change bounded MC tests: roughly 6.6 s each across three tests
- post-change shared fixture: one panel completion gap about 6.9 s
- the two redundant full panel executions disappeared

Decision:

**SHARE_CLASS_LEVEL_MONTE_CARLO_FIXTURE**

Claim ceiling:

**TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY**
