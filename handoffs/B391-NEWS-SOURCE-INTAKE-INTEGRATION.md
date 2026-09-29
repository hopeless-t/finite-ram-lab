# B391 — News/source intake integration

## Status

SOURCE INTAKES REVIEWED / COUNCIL ADDENDUM CONVERGED.

No physical experiment launched.

## Reviewed existing source intakes

Primary repository documents:

- docs/AI-WORKER-FINITE-WORKING-SET-INTAKE-2026-09-29.md
- docs/NAIVE-N05-FLASH-INTAKE-v1.md

The first intake includes source observations from:
- Strands context management/offloader
- OpenAI Tool Search
- AI-generated-summary human-memory study
- Tabelog staged decision questions
- Cloudflare cf CLI capability search
- GPT Researcher Jev context filtering/evals
- Claude eval/hillclimb guidance

The second intake contributes:
- retention vs sparse access
- semantic reuse distance
- reconstructible bulk vs retained metadata
- end-to-end cost accounting

## Council delta

B390 generic control state gained three independent dimensions:

- restore fidelity / source recoverability
- reuse horizon
- access/movement intensity

This yields the working generic state:

tier
+ owner/lease
+ hotness
+ predicted next use
+ transfer cost
+ restoration cost
+ restoration fidelity
+ reuse horizon
+ access/movement intensity
+ interference
+ bottleneck regime

## New principles absorbed

1. addressable universe != resident working set
2. resident footprint != bytes touched != bytes moved
3. restore cost != restore fidelity
4. age != semantic reuse horizon
5. exact pointer-backed offload != lossy summary
6. reconstructible bulk and irreplaceable metadata deserve different retention policies

## Domain guards

Not absorbed into physical-memory evidence:

- human false-memory mechanism
- AI-context semantics as a physical RAM mechanism
- tool execution authority

Authority remains outside finite-ram core.

## New branch candidates

Generic:
- REUSE-001
- TRAFFIC-001
- FIDELITY-001

AI-worker/application:
- AIWS-001 reversible offload vs lossy summary
- AIWS-002 semantic hotness vs recency
- AIWS-003 adaptive prefetch depth
- AIWS-005 usefulness vs similarity selection

No branch is authorized for execution.

## Updated

- docs/FRL-STATE-TRANSITION-MODEL-v0.md
- docs/COUNCIL-2026-09-30-FRL-TRANSFER-v1.md
