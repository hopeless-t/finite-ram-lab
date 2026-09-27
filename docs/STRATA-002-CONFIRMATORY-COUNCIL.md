# STRATA-002 Confirmatory Council

> **Status:** COUNCIL CONVERGED / MONTE CARLO SIZING AUTHORIZED
> **Parent evidence:** STRATA-002-PILOT-v1

## Pilot facts

Across 8 independent runner blocks, `buffered_dontneed` vs ordinary `buffered` produced:

- MemoryHigh-event differences: `[-6,-5,-5,-5,-5,-5,-6,-6]`;
- median post-scan `memory.current` difference: about `-82.98 MiB`;
- median post-scan file-residency difference: about `-0.8646`;
- HOT anonymous residency remained 1.0;
- scan-time ratio median: about `1.027`;
- geometric-mean scan-time ratio: about `1.005`;
- substantial block-to-block timing variance.

NOREUSE did not materially change the pressure outcome and does not advance.

O_DIRECT remains a reference arm, not the production target.

## Practical confirmatory question

Can sliding `POSIX_FADV_DONTNEED` on a normal buffered one-shot stream reproducibly reduce memory pressure by a practically meaningful amount without imposing an unacceptable scan-time penalty?

## Efficacy event

Define a block-level pressure-efficacy success as:

`memory.current(buffered) - memory.current(dontneed) >= 64 MiB`

Why 64 MiB:

- it is smaller than the ~83 MiB pilot median;
- it represents reclaiming at least two-thirds of the 96 MiB COLD file footprint;
- it is large enough to matter on finite-RAM personal systems;
- it does not require reproducing the full pilot effect.

The confirmatory efficacy gate will use an exact one-sided sign test against `p=0.5`.

Familywise alpha budget for this primary gate:

`0.025`

## Mechanism-fidelity gate

Also require:

- median DONTNEED post-scan file residency <= 0.10;
- median ordinary-buffered post-scan file residency >= 0.50;
- no OOM;
- no HOT-content corruption;
- no advice failure.

This confirms the tested mechanism actually operated.

## Latency-risk guardrail

Pressure reduction alone is insufficient for a practical helper.

Define the paired scan-time ratio:

`scan_ms(dontneed) / scan_ms(buffered)`

Primary latency summary:

geometric mean across independent blocks.

Practical guardrail target:

`ratio <= 1.25`

Interpretation:

a helper that requires more than roughly 25% sustained scan overhead would need stronger application-specific justification before personal-PC deployment.

Because hosted-runner timing is noisy, this guardrail is used for design sizing and later interpretation rather than to erase a clear pressure mechanism result.

## Pilot uncertainty treatment

The pilot observed 8/8 efficacy successes at the 64 MiB threshold.

Do not size from `p=1.0`.

Use the exact one-sided 95% Clopper-Pearson lower bound for 8/8:

approximately `0.687656`

as the conservative efficacy success probability in the design-assurance simulation.

For latency:

- use pilot paired log scan ratios;
- preserve their observed variance;
- evaluate the probability that a one-sided 95% upper bound on the mean log ratio is <= `log(1.25)`.

## Candidate confirmatory block counts

Evaluate:

`16, 24, 32, 40, 48, 56, 64, 72`

## Selection rule

A candidate N earns confirmatory consideration only if Monte Carlo estimates at least 80% probability of satisfying:

1. efficacy exact-sign gate at alpha 0.025 under conservative success probability;
2. latency guardrail under the pilot-derived log-ratio model.

Mechanism-fidelity checks are not probabilistically waived.

## Cost / external-validity Council seat

If the first N meeting the rule is large, do **not** automatically launch it.

The hosted environment may cease to be the best next investment because the actual product target is a personal Linux PC.

A large hosted confirmatory requirement should trigger a comparison between:

- hosted confirmatory cost;
- a smaller hosted replication;
- MVCA-gated local dogfood / external-validity study.

Proposal is not authority.

## Decision

Run STRATA-002 confirmatory design Monte Carlo now.

Do not launch the physical confirmatory experiment automatically.

## Authority boundary

Design analysis only.
