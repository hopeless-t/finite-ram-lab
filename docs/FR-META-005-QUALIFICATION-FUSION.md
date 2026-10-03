# FR-META-005 — Qualification Fusion

Status: **DOGFOOD PROTOCOL CANDIDATE**

Parent: **FR-META-004**

## Bottleneck

FR-META-004 reduced per-file publication fan-out, but a clean implementation
push still launches both the repository-wide CI workflow and a dedicated
research qualification workflow.

The dedicated workflow repeats checkout, Python setup, installation, and often
unit tests that general CI already performs.

## Change

General CI now auto-discovers changed modules matching
src/finite_ram_lab/fr_meta_*.py.

A matching module must expose run_panel() returning a dict whose status is PASS.

CI writes the complete result into a meta-qualification artifact.

Future meta lanes using this convention therefore do not need a dedicated
workflow.

## Clean lifecycle

Historical #103-#105 baseline: 10 workflow runs.

FR-META-004 atomic plus dedicated workflow: 4 workflow runs.

FR-META-005 fused path:

1. implementation push -> 1 general CI
2. receipt push -> 1 general CI
3. PR open -> 1 general CI

Total: 3 workflow runs.

That is 70 percent fewer runs than the observed historical baseline and
25 percent fewer than the atomic-plus-dedicated clean path.

A fix commit also costs one CI run instead of two.

## Why Monte Carlo is skipped here

The workflow topology is exact for this routing question. No uncertain
parameter changes the fact that one workflow is fewer than two while preserving
the same general CI safety surface.

Running Monte Carlo here would add research friction without decision value.

This is deliberate dogfood of the L1 rule: Monte Carlo is conditional on value
of information, not a ritual stage.

## Safety boundary

General CI is not removed.

The qualifier fails closed if a changed meta module lacks run_panel, run_panel
throws, the result is not a dict, or status is not PASS.

The complete result remains an Actions artifact.

This does not change execution authority or branch protection policy.

## Claim ceiling

**CI_QUALIFICATION_FANOUT_OPTIMIZATION_ONLY**
