# B500 — One-Shot Adaptive Local Governor Qualification v0.1

Status: **SINGLE-COMMAND LOCAL QUALIFICATION PIPELINE**.

## 1. Goal

B496-B499 established the pieces needed for a local Governor.

B500 composes them into one bounded command suitable for a single approved
MVCA/LDC execution.

## 2. Full default command

```bash
frl local-qualify \
  --exploration-samples-per-q 8 \
  --size 2048 \
  --target-rank-coverage 0.95 \
  --max-extension-cycles 4 \
  --out-dir local-governor-bundle
```

## 3. Adaptive algorithm

The command performs:

1. n8 exploration over q={1,2,4,7};
2. compute local Pareto;
3. compute each Pareto q evidence deficit to the requested coverage;
4. add only those missing fresh-process samples;
5. recompute Pareto;
6. if a previously dominated under-sampled q re-enters, fill only its deficit;
7. repeat until every final Pareto q is evidence-qualified;
8. promote the fingerprint-bound local policy.

## 4. Bounded work

For 95% rank-max coverage:

`n_required = 19`.

With four candidate q values, no q needs more than 19 total samples.

Default maximum physical observations are therefore:

`4 * 19 = 76`.

The normal cost is lower when the local Pareto has fewer than four points.

## 5. Evidence integrity

Every adaptive extension cycle enforces:

- current host fingerprint matches the exploration binding;
- fingerprint remains stable after the cycle;
- exact numerical semantics;
- output digest equals the frozen local workload digest;
- no hosted threshold import.

## 6. Output bundle

B500 writes:

- `local-exploration.json`
- `local-calibration-state.json`
- `local-governor-policy.json`
- `local-qualification-receipt.json`
- `bundle-manifest.json`

The manifest contains SHA256 values for all four core artifacts.

## 7. Qualification receipt

The receipt records:

- host fingerprint SHA;
- initial observation count;
- every adaptive extension cycle;
- total physical observations;
- final local Pareto;
- final per-q sample counts;
- target coverage;
- policy ID;
- calibration-state digest;
- policy digest.

## 8. Why this is the LDC-friendly form

The local operator no longer needs to manually run:

```text
bootstrap
-> exploration
-> inspect Pareto
-> calculate deficits
-> extension
-> inspect again
-> promote
```

B500 turns that workflow into one deterministic bounded command.

This minimizes authority/friction surface while preserving all intermediate
evidence artifacts.

## 9. Claim ceiling

**HOST_BOUND_LOCAL_GOVERNOR_QUALIFICATION**

## 10. Current execution status

The actual development-machine run still requires an admitted MVCA/LDC action.

The latest readback before B500 still reported:

`operator_binding_missing`

and no authority grant for this lane.

No unrelated action authority is reused.

## 11. Next

Once the local binding/action is available, execute B500 once through MVCA/LDC
and return the bundle manifest.

The next research step can then compare the local q topology against the hosted
topology without assuming either one is universal.
