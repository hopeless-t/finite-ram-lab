# STRATA-002 Confirmatory Design Monte Carlo v1 — Result

> **Status:** PASS / DESIGN ONLY
> **Run:** `36339291206`
> **Artifact:** `STRATA-002-CONFIRMATORY-MC-36339291206`
> **Artifact id:** `10938072946`
> **Artifact digest:** `sha256:74537b78b37f9d05ee9deaf381c29989d69eab43af140f7493907d883ac70561`

## Frozen design inputs

- conservative efficacy success probability: `0.687656`
- pilot geometric-mean scan ratio DONTNEED / buffered: `1.0048`
- pilot paired log-ratio sample SD: `0.7606`
- latency guardrail: one-sided 95% upper bound <= `1.25x`
- target joint design assurance: `0.80`
- 200,000 Monte Carlo replicates per candidate

## Results

| Blocks | Efficacy assurance | Latency assurance | Joint assurance |
| ---: | ---: | ---: | ---: |
| 16 | 0.2135 | 0.2915 | 0.0625 |
| 24 | 0.3393 | 0.3876 | 0.1315 |
| 32 | 0.4350 | 0.4765 | 0.2075 |
| 40 | 0.6406 | 0.5557 | 0.3553 |
| 48 | 0.6871 | 0.6243 | 0.4294 |
| 56 | 0.8085 | 0.6827 | 0.5517 |
| 64 | 0.8278 | 0.7348 | 0.6084 |
| 72 | 0.8969 | 0.7785 | 0.6989 |

Selection:

`NONE_WITHIN_FROZEN_RANGE`

## Interpretation

The pressure-efficacy side becomes strong with larger N.

At 56 blocks the conservative efficacy design assurance already exceeds 80%.

The joint design fails because hosted-runner timing variance remains large.

Even at 72 blocks:

- efficacy assurance: ~89.7%
- latency assurance: ~77.8%
- joint assurance: ~69.9%

Therefore extending a hosted confirmatory campaign primarily to resolve latency would be inefficient.

## Decision

Do **not** automatically extend the hosted block grid.

The next higher-information step is a local external-validity design on the actual personal Linux machine, where:

- storage hardware is stable;
- kernel/filesystem are stable;
- background workload can be characterized;
- timing variance is directly relevant to the product target.

A smaller hosted replication remains possible later if the local result disagrees with the mechanism.

## Authority boundary

This result authorizes no local execution and no physical confirmatory campaign.
