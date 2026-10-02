# B500 — Adaptive One-Shot Local Governor Qualifier Receipt

Status: **PASS / ONE-SHOT LOCAL QUALIFIER QUALIFIED**

## Frozen qualification

- workflow run: 36967069106
- job: 110713017446
- execution head: 113749f593f1c4417d548aeee72884e73b7e441f
- targeted tests: 4/4 PASS
- ordinary CI: PASS
- artifact ID: 11210402309
- artifact ZIP SHA256: 043a631d8acea1be366de593756765c173dd76d53b3a58772d9cc6b83d7da8b0
- bundle manifest SHA256: d0a5f16122514a9153594a4c3ed7c827e4db7ef1c882530ef6820cffbccf2d06
- bound decision SHA256: afad4055e1fc21e721a272304840931a8d8865bf06c2e6757ab1a9cdb3874322

## What B500 qualifies

B500 collapses the full local research/application path into one bounded command:

```text
initial all-q exploration
-> local Pareto discovery
-> add only currently under-sampled Pareto q
-> recompute Pareto
-> repeat if a previously dominated q re-enters
-> stop when every final Pareto q meets the requested evidence target
-> promote fingerprint-bound local policy
-> emit policy + calibration state + exploration + qualification receipt
-> validate the promoted policy with the bound selector
```

CLI:

```bash
frl local-qualify \
  --exploration-samples-per-q 8 \
  --size 2048 \
  --target-rank-coverage 0.95 \
  --max-extension-cycles 4 \
  --out-dir local-governor-bundle
```

## Hosted qualification smoke

The GitHub Actions qualification intentionally used a small smoke configuration:

- exploration samples/q = 2
- size = 64
- target coverage = 0.75
- max extension cycles = 4

Observed smoke outcome:

- final Pareto = {q2, q7}
- total physical observations = 10
- generated policy ID = local-governor-edb2af10e557-v1
- environment binding validated by local-governor-select

The smoke bundle was successfully consumed by the fingerprint-bound selector.

## Evidence boundary

The hosted smoke proves executable orchestration only.

It is **not** development-machine calibration.

No GitHub-hosted peak thresholds or hosted Pareto result is promoted as a local
development-machine fact.

## Full development-machine bound

At the intended 95% configuration:

- initial exploration = 8 * 4 = 32 observations
- target n = 19 per final Pareto q
- worst case: all four q remain Pareto
- maximum total observations = 19 * 4 = 76

The adaptive path can use fewer observations whenever the local Pareto contains
fewer than four q values.

## Bundle

B500 writes:

- local-exploration.json
- local-calibration-state.json
- local-governor-policy.json
- local-qualification-receipt.json
- bundle-manifest.json

The manifest cryptographically binds the generated bundle files.

## Current real-machine blocker

The latest MVCA/LDC preflight still reports:

- MVCA CURRENT
- clean working tree
- LDC config UNKNOWN
- reason: operator_binding_missing
- authority_grant: NONE

No unrelated authority is consumed.

## Claim ceiling

**HOST_BOUND_LOCAL_GOVERNOR_QUALIFICATION**

## Next

B501 should prepare the explicit MVCA/LDC execution-admission handoff for this
single bounded local qualification command.

Once the appropriate operator binding/action is available, the development
machine can run the full B500 command without redesigning the experiment.
