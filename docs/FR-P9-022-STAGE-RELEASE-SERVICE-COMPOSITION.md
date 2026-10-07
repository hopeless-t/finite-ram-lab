# FR-P9-022 — Stage-release-aware service composition

## Prior-art boundary first

Service curves, min-plus algebra, service-curve composition, delay bounds and SCED are established Network Calculus / real-time-systems prior art. FR-P9-022 does **not** claim to invent those concepts or a new theorem.

The narrower Part9 question is: how should a Semantic Residency Compiler represent **semantic materialization stage dependencies** so it does not count resource service that arrived before the dependent semantic state existed?

## Problem exposed by P9-021

P9-021 physically used a sequential transfer -> CPU pipeline. A planning model that checks only absolute per-resource totals can still be wrong:

```text
transfer by final deadline: sufficient
CPU service by final deadline: sufficient
```

may be true even when all CPU service occurred **before** transfer completed. If unused CPU capacity cannot be banked, that service is unavailable to the reconstruction stage.

## Bounded discrete operator

For transfer demand `W_t`, find the first index `R` where transfer cumulative service reaches `W_t`.

Then count only CPU service delivered after release:

```text
usable_cpu(D) = S_cpu(D) - S_cpu(R)
```

and admit only if:

```text
R exists by D
and usable_cpu(D) >= W_cpu
and both service epochs are current
```

This is a deliberately simple no-banking, sequential-stage model. It is not proposed as a replacement for Network Calculus composition.

## Frozen adversary

```text
TRANSFER = (0,0,4,0)  -> completes at bin 3
CPU_FRONT = (4,0,0,0)
CPU_BACK  = (0,0,0,4)
final deadline = bin 4
requirements = transfer 4, CPU 4
```

An independent absolute check admits CPU_FRONT because both horizon totals are sufficient. Stage-aware admission rejects it because usable CPU after transfer release is zero. CPU_BACK is admitted.

## Qualification

- exhaustive discrete comparison against a direct sequential-simulation oracle;
- stale upstream-stage epoch adversary;
- deterministic Monte Carlo comparing independent absolute checks with release-aware admission.

## Architectural consequence

A materialization plan needs not only a vector of typed resources, but also a dependency graph / release relation:

```text
cold bytes --TRANSFER--> runtime representation
                           |
                           v release
                       CPU reconstruction
                           |
                           v release
                       verification
                           |
                           v
                       device placement
```

Future physical work should test partial streaming/overlap, where downstream work can begin after a prefix rather than after the entire upstream stage.

Claim ceiling:
`ANALYTIC_DISCRETE_TWO_STAGE_RELEASE_AWARE_MATERIALIZATION_ONLY_NO_NEW_NETWORK_CALCULUS_THEOREM_OR_PHYSICAL_APPLICATION_CLAIM`
