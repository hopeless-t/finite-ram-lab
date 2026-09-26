# Bounce Handoff

> **Bounce ID:** B031  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Launch the frozen VAL-003 catastrophic-tail validation without changing the pre-registered design or endpoint.

## Canonical inputs

- `handoffs/B030-VIS001-TOOL-COUNCIL.md`
- `findings/VAL-003-design-study.md`
- `docs/VAL-003-DESIGN.md`
- `docs/VAL-003.md`
- `specs/VAL-003.json`
- `findings/EXP-002-initial.md`

## Frozen design

- 40 independent GitHub-hosted runner blocks;
- 10 CORRECT_PAGEOUT trials per block;
- 10 NO_HINT trials per block;
- 800 total trials;
- 164 MiB MemoryHigh;
- 320 MiB MemoryMax;
- catastrophic endpoint fixed at HOT retouch >= 500 ms;
- 1,000,000-draw deterministic sign-flip randomization test;
- 20,000-resample cluster bootstrap.

## Completed

- added `.github/workflows/val-003.yml`;
- preserved the frozen endpoint and design exactly;
- launched the confirmatory workflow.

## Workflow

- launch commit: `8b16ae39aff7209ff6280e94491ee0c1fc306a64`
- run: `36241864223`

## Next recommended bounce

> Read the completed VAL-003 result using only the frozen analysis, write the finding, update repository status, write the next handoff, and stop.

## Authority boundary

Launching the workflow is not evidence for or against the tail-risk hypothesis.

EXP-002 remains motivation only; its trials are not pooled into VAL-003.
