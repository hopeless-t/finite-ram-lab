# Bounce Handoff

> **Bounce ID:** B022  
> **Status:** COMPLETE

## Objective

Classify PAGEOUT preparation under natural transition-zone pressure.

## Evidence

- run: `36228551661`;
- 8 runner blocks / 16 trials;
- exact sign-flip p = 0.0078125;
- target median residency after burst = 0.62183;
- matched control median residency = 1.0;
- median target-control difference = -0.37817.

## Frozen finding

`MADV_PAGEOUT` preparation is **EFFECTIVE** at steering subsequent natural reclaim in this hosted workload.

`MADV_COLD` was ineffective under the corresponding probe.

## Next recommended bounce

> Design the first semantic-information performance experiment with three arms: CORRECT_PAGEOUT, WRONG_PAGEOUT, and NO_HINT.

All arms must experience the same natural 164 MiB pressure and the same future HOT reuse.

Include PAGEOUT call overhead in a secondary end-to-end cost metric; keep HOT retouch latency as the mechanism-sensitive outcome.

Use Monte Carlo to freeze runner/repeat allocation before launching.

## Authority boundary

Steering residency is not yet evidence of net application benefit or of a need for a coordination service.
