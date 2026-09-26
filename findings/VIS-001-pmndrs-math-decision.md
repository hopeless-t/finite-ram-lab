# VIS-001 Tool Decision — pmndrs/math

> **Status:** FROZEN TOOLING DECISION  
> **Evidence class:** cross-repository qualification + architecture review

## Decision

`pmndrs/math@0.1.0` is accepted as a **Qualified Optional Visualization Dependency** for Finite RAM Lab.

It is not accepted into the scientific core, repository root dependency set, canonical evidence pipeline, or global AI-worker tool surface.

## Why

The existing `finite-tool-surface-lab` dogfood already established that the package is usable in a clean hosted runner, modest in footprint, dependency-light in the observed package, compatible with caller-owned/in-place numeric patterns, and ships an Agent Skill.

Finite RAM Lab has a concrete potential use that matches the package better than the scientific core does:

> interactive evidence replay.

## Why not install globally now

The package cost is not just its unpacked size.

Global installation would add:

- a Node runtime seam;
- package lifecycle / lockfile maintenance;
- supply-chain surface;
- additional worker-visible capability.

Those costs exist even when no visualization task needs the package.

## Why no decision Monte Carlo

The remaining uncertainty is primarily about future usefulness and contributor comprehension, not a calibrated stochastic process.

A Monte Carlo over invented priors would add false precision.

The next evidence should come from one real VIS-001 replay dogfood.

## Authorized action

When VIS-001 begins, it may create an isolated `explorer/` package and pin `pmndrs/math@0.1.0`.

The explorer may consume canonical evidence read-only.

## Not authorized

This decision does not authorize:

- moving scientific calculations to JS/TS;
- replacing NumPy/SciPy;
- exposing `pmndrs/math` to every worker;
- treating visualization output as scientific evidence;
- building a large dashboard before the one-replay dogfood passes.

## Cross-repository qualification provenance

- `finite-tool-surface-lab` branch: `research/dogfood-pmndrs-math-v0`
- result commit: `31bea58625dfddd8f7f8c538665274795a426e7a`
- Actions run: `36231954801`
- artifact: `10902529835`
- artifact SHA-256: `06a9fa99880e36826ab5e16a58fd84032d7806af583f5a7d5a928e8bfd7b8f86`

## Next visualization question

> Can a single interactive replay make one canonical memory-pressure experiment substantially easier for a third party to understand and inspect?
