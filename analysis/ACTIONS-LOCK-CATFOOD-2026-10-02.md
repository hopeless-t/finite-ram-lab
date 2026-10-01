# ACTIONS-LOCK-001 — GitHub Actions dependency pinning Catfood

Primary format source: `github/actions-lockfile` public preview.
Current lock schema observed: `v0.0.3`.

The official lockfile records the resolved transitive dependency graph for
workflows, including exact action commits. The format is pre-1.0 and may still
change.

Catfood started with the repository itself instead of enabling the preview tool
blindly. A live source inspection of `finite-ram-lab` found many workflows
using mutable refs such as:

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/upload-artifact@v7`
- `actions/download-artifact@v8`

This candidate adds only a read-only direct-reference auditor. It does not edit
workflow YAML, install `gh actions-lock`, resolve transitive actions, or mint an
`actions.lock` file.

If the direct audit proves useful, the next experiment is to run the official
preview producer in a disposable branch and compare its transitive graph against
this preflight before considering adoption.
