# KSLA-BENCH-001 — World Claim Gate Receipt

Status: **PASS / UNIVERSAL STANDARD-SPD WORLD-BEST CLAIM REJECTED**

## Qualification

- workflow run: 37100991192
- job: 111140322271
- execution head: e24fb54e9b12c185a5ecc63c40cd1e7ed82cb0fa
- artifact ID: 11265936742
- artifact ZIP SHA256: faba4c9f1d9463b1892cc7509c01b552d371325a236246116ebfab10c5464e01
- spec SHA256: 10762da7c9897156d9eb03362818900f1acb3594325539c3a61d3971367fcf8d
- result SHA256: 52680599a38f99a8d07709bef9158310c8fe8eb732fe33a3a39282edfd452e98

## Hosted-runner result

| n | CG median s | sparse-direct median s | KSLA median s | KSLA/CG | KSLA/direct |
|---:|---:|---:|---:|---:|---:|
| 64 | 0.000606 | 0.0000846 | 0.007798 | 12.86x | 92.17x |
| 256 | 0.000569 | 0.000150 | 0.042093 | 73.94x | 281.52x |
| 1024 | 0.000501 | 0.000585 | 0.214464 | 428.09x | 366.83x |
| 4096 | 0.000733 | 0.002002 | 0.870762 | 1188.45x | 434.91x |

All KSLA arms reached exact integer zero residual.

CG converged in 16 iterations at every frozen size.

## Verdict

The claim:

`KSLA is already the world's fastest / cheapest ordinary sparse-SPD solver`

is **NOT SUPPORTED**.

This is a successful falsification gate, not a failed benchmark.

## Surviving hypothesis

KSLA retains a different systems hypothesis:

- zero-intelligence proposal source;
- local validation;
- exact rejection of harmful local actions in the frozen fixture;
- tiny logical-kitten state;
- finite-residency scheduling;
- future heterogeneous / stale / corrupt / remote action sources.

Therefore the remaining candidate frontier is not ordinary solver speed.

It is:

`verified heterogeneous algorithm portfolio under bounded residency and unreliable proposal sources`.

## Architectural consequence

CG, sparse direct, Kaczmarz++, Random Pursuit, Ozaki, low precision, exact
fallback, and random actions should be modeled as **proposal species** under a
shared verifier / resource governor.

KSLA should not attempt to replace every numerical method.

It should choose, combine, reject, or escalate among them.

## Claim ceiling

**HOSTED_RUNNER_BENCHMARK_GATE_ONLY**
