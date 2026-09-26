# Bounce Handoff

> **Bounce ID:** B016  
> **Status:** COMPLETE

## Objective

Read the EXP-001 design Monte Carlo and freeze one causal experiment design.

## Evidence

- design run: `36228047531`;
- D2_8x2: 32 trials, worst 5x detection ≈ 0.967;
- D3/D4 cost 48 trials;
- D1 did not provide adequate conservative large-effect sensitivity.

## Frozen decision

Use D2_8x2:

    8 runner blocks
    2 HOT_EVICT trials/block
    2 COLD_EVICT trials/block
    32 total trials

Primary analysis: exact block sign-flip on mean log-latency contrast.

## Next recommended bounce

> Implement EXP-001 exactly as frozen and launch it without post-hoc design changes.

## Authority boundary

The Monte Carlo selected an experiment design; it did not support the causal hypothesis.
