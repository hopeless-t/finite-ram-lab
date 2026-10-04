# FR-FP-026 Receipt

Status: **PASS / ANALYTIC REUSE-PROBABILITY CEILING QUALIFIED**

Parent: **FR-FP-025**

- workflow run: 37192575736
- job: 111407689710
- execution head: 1e358ee08f70ae60483e78bf6da0ca16cb908d96
- comparisons: 14,400
- mismatches: 0
- reused hosted runs: 15
- residual samples: 60
- WARM samples: 90
- new physical runs: 0

Analytic reduction:

    cost bound:
      p <= 8 MiB * lambda / E[(bR-W)+]

    deadline bound:
      p <= epsilon / P(bR>D)

    combined:
      p <= min(1, cost bound, deadline bound)

The analytic reuse ceiling exactly reproduced the direct FR-FP-025 WARM/COLD
eligibility decision across the full frozen comparison grid.

Representative cells:

- fast / loose:
  - b=3 ms, lambda=0.5 ms/MiB, D=50 ms, epsilon=0.10
  - p ceiling = 0.84448
  - expected-cost constraint binds

- mid / tight:
  - b=10 ms, lambda=1.0 ms/MiB, D=25 ms, epsilon=0.05
  - p ceiling = 0.30
  - deadline-risk constraint binds

- slow / strict:
  - b=100 ms, lambda=10 ms/MiB, D=100 ms, epsilon=0.05
  - p ceiling = 0.08333
  - deadline-risk constraint binds

Decision:

**REPLACE_EXACT_REUSE_POINT_ESTIMATION_WITH_A_SAFE_REUSE_UPPER_BOUND_WHEN_ROUTING_WARM_VS_COLD**

Governor consequence:

The workload learner no longer needs an exact reuse-probability point estimate.

It only needs a safe upper confidence bound that can be compared with the
decision-specific reuse ceiling.

Claim ceiling:

**ANALYTIC_REDUCTION_OF_FR_FP_025_EMPIRICAL_8MIB_FRONTIER_ONLY**
