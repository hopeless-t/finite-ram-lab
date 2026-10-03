# FR-META-011 Receipt

Status: **PASS / RECURSIVE PANEL FIXTURE REUSE VALIDATED**

- workflow run: 37137996360
- job: 111246367899
- execution head: 9e0c6e7a82c710b57763c1da4f33ac4504e56e5b
- qualification artifact ID: 11279380838
- artifact ZIP SHA256: ed612724e937b2d03cd6b3b95231fc56df203227867ec7dc8a17cda833b32ad9

Evaluator semantics unchanged:

- objective-weight perturbations per panel: 300
- holdout: unchanged
- Goodhart negative control: unchanged
- promotion gates: unchanged
- pseudo-Council: unchanged

Test-harness work:

- baseline recursive run_panel calls: 2
- candidate calls: 1
- structural duplicate panel reduction: 50%

Observed CI:

- prior specimens showed two roughly 3.2 s recursive-panel completion gaps;
- shared-fixture specimen shows one roughly 3.29 s panel completion gap;
- the second full L2 campaign disappeared.

Decision:

**SHARE_RECURSIVE_RESEARCH_PANEL_WITHIN_TEST_CLASS**

Claim ceiling:

**TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY**
