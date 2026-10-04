# FR-FP-025 Receipt

Status: **PASS / RISK-AWARE WARM-COLD TIER FRONTIER QUALIFIED**

Parent: **FR-FP-024**

- workflow run: 37192331251
- job: 111406967996
- execution head: a5ca042e9f0a535e31b443682415426612777a10
- source runs: 15
- state size: 8 MiB
- residual samples: 60
- WARM samples: 90
- new physical runs: 0

Decision law:

    lambda_star
      =
    p * E[(bR - W)+] / 8 MiB

and independently:

    q_D
      =
    p * P(bR > D)

COLD is eligible only when:

    external lambda >= lambda_star
    AND
    q_D <= external miss tolerance epsilon

where:
- b = calibrated current-run COLD baseline;
- R = residual multiplier prior;
- W = WARM restore prior;
- p = reuse probability;
- D = deadline.

## Representative cells

Fast current run / low reuse:
- b = 3 ms
- p = 0.10
- conditional expected COLD-WARM penalty: 4.737 ms
- lambda_star: 0.0592 ms/MiB
- 10 ms unconditional deadline risk: 1.33%
- 25/50/100 ms risk: 0%

Middle:
- b = 10 ms
- p = 0.50
- conditional expected penalty: 17.566 ms
- lambda_star: 1.0979 ms/MiB
- 10 ms risk: 30.0%
- 25 ms risk: 8.33%
- 50 ms risk: 5.83%
- 100 ms risk: 0%

Slow current run / certain reuse:
- b = 100 ms
- p = 1.00
- conditional expected penalty: 182.510 ms
- lambda_star: 22.8138 ms/MiB
- 10/25/50 ms risk: 100%
- 100 ms risk: 60%

## Structural checks

Qualified:
- lambda_star increases monotonically with reuse probability;
- lambda_star increases monotonically with current-run baseline;
- deadline risk increases monotonically with baseline;
- deadline risk decreases monotonically as deadline relaxes.

## Theory update

A WARM/COLD choice cannot be represented safely by one fixed latency threshold.

The Governor needs two independent constraints:

1. expected memory-vs-promotion-cost break-even;
2. deadline-tail eligibility.

Do not collapse them into one hidden universal utility.

Decision:

**ROUTE_WARM_VS_COLD_WITH_SEPARATE_MEMORY_SHADOW_PRICE_AND_DEADLINE_RISK_CONSTRAINTS**

Claim ceiling:

**EMPIRICAL_FRONTIER_FROM_REUSED_8MIB_HOSTED_RESTORE_EVIDENCE_ONLY**
