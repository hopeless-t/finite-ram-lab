# KSLA-BENCH-001 — World Claim Gate

This benchmark intentionally tries to falsify the strongest marketing claim.

Question:

> Is KSLA already the world's cheapest and strongest general computation model?

For ordinary sparse symmetric-positive-definite linear systems, the benchmark
compares:

- SciPy conjugate gradient;
- SciPy sparse direct solve;
- KSLA batch-8 imaginary-kitten search.

The fixture uses the same tridiagonal SPD family as KSLA-002 at dimensions
64, 256, 1024 and 4096.

The benchmark records median hosted-runner wall time, exactness / residual, and
abstract local-touch proxies.

## Claim rule

A standard sparse-SPD "world best" claim is rejected if KSLA does not beat both
standard baselines on every tested size.

This gate is intentionally hostile to hype.

## Why a loss is scientifically useful

CG and sparse direct solvers receive the matrix explicitly and exploit its
linear-algebraic structure.

KSLA deliberately gives its imaginary kittens no matrix, gradient, objective,
or state.

Therefore a standard-solver loss does not invalidate the systems hypothesis.

It narrows the hypothesis to a different frontier:

- tiny local access;
- effectively stateless proposal generation;
- external verification;
- selective rejection;
- finite residency;
- future stale/corrupt/faulty proposal tolerance.

The next benchmark must compare against modern randomized Kaczmarz / CD++ and
zeroth-order methods under matched information-access contracts.

## External state of the art

Recent work remains strong. Kaczmarz++ / CD++ reports arithmetic competitiveness
with CG and GMRES on benchmark problems, and 2026 work continues to improve
residual-based, parameterized, and block Kaczmarz variants.

Therefore no "world best" claim is permitted from a synthetic in-house fixture
alone.

## Claim ceiling

HOSTED_RUNNER_BENCHMARK_GATE_ONLY
