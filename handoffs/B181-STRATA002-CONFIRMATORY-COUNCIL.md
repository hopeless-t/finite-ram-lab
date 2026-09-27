# Bounce Handoff

> **Bounce ID:** B181
> **Status:** COMPLETE / STRATA-002 CONFIRMATORY COUNCIL CONVERGED

## Primary efficacy threshold

Per independent block:

`buffered memory.current - DONTNEED memory.current >= 64 MiB`

Exact one-sided sign test vs p=0.5, alpha 0.025.

## Conservative design probability

Pilot: 8/8 efficacy successes.

Sizing uses exact one-sided 95% lower bound:

`p = 0.687656...`

not p=1.0.

## Latency guardrail

Geometric mean scan ratio DONTNEED / buffered <= 1.25.

Use pilot paired log-ratio variance.

## Candidate N

16, 24, 32, 40, 48, 56, 64, 72 blocks.

## Selection

Need >=80% Monte Carlo joint design assurance.

Do not auto-launch a large confirmatory campaign.

## Next action

Freeze and implement Monte Carlo sizing.

## Authority boundary

Design analysis only.
