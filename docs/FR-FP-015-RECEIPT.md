# FR-FP-015 Receipt

Status: **PASS / ANALYTIC WARM-COLD BREAK-EVEN FRONTIER QUALIFIED**

Parent: **FR-FP-014**

- workflow run: 37145574901
- execution head: ea1f5f7dde5de0c3fff9dde8a53b4b9c5d9a8138
- source evidence: FR-FP-014 / PR #133

Measured inputs:
- WARM median read: 847,494 ns
- COLD median read: 3,102,932.5 ns
- restore penalty: 2,255,438.5 ns
- page-cache residency difference: 8 MiB

Break-even law:

    lambda_star(p)
      = p * (L_cold - L_warm)
          / (M_warm - M_cold)

Frozen coefficient:

    lambda_star(p)
      = p * 281.9298125 us/MiB

Examples:
- reuse p=0.05 -> 14.096 us/MiB
- reuse p=0.10 -> 28.193 us/MiB
- reuse p=0.25 -> 70.482 us/MiB
- reuse p=0.50 -> 140.965 us/MiB
- reuse p=1.00 -> 281.930 us/MiB

Interpretation:

No universal WARM/COLD winner is selected.

The tier decision depends explicitly on:
- state reuse probability;
- task-specific shadow price of resident memory;
- measured restore-cost difference.

Decision:

**KEEP_MEMORY_SHADOW_PRICE_AND_REUSE_PROBABILITY_EXPLICIT_INSTEAD_OF_HIDING_THEM_IN_A_SINGLE_TIER_SCORE**

Next:

Measure WARM/COLD restore cost across multiple state sizes and determine whether
restore latency can be represented as a size-dependent cost law.

Claim ceiling:

**ANALYTIC_BREAK_EVEN_FRONTIER_FROM_SINGLE_HOSTED_RESTORE_PILOT_ONLY**
