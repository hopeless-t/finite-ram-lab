# B497 — Local Calibration Exploration Harness Receipt

Status: **PASS / HARNESS QUALIFIED, LOCAL MACHINE EVIDENCE NOT YET CLAIMED**

## Frozen qualification

- workflow run: 36965974663
- job: 110709687056
- execution head: f761958e33a0817692b023d08f27b3af6f184a35
- tests: 4/4 PASS
- artifact ID: 11209373465
- artifact ZIP SHA256: d22a7577833f052e948cd7032d1d5112d611c6b0ace38df1374f6e503f14521d
- hosted harness smoke SHA256: 8cac021da39f79c6d2efecedadf508401801a7529fbdae8968c253e9226e2720

## What was qualified

The command:

```text
frl local-calibrate
```

now implements:

- q={1,2,4,7}
- fresh child process execution
- order-balanced full n8 design
- exact semantic gate
- cross-q output-digest gate
- pre/post host-fingerprint stability gate
- local median peak/latency frontier
- local Pareto calculation
- promotion-budget calculation

## CI smoke scope

The qualification workflow intentionally used only:

- 2 samples per q
- size64
- 8 physical observations

on a GitHub-hosted runner.

This proves the executable harness path, not the development-machine memory
surface.

The result explicitly kept:

`policy_promotion_allowed = false`

and no local development-machine policy is claimed.

## Full local command

Once an appropriate MVCA/LDC action is admitted:

```bash
frl local-calibrate \
  --samples-per-q 8 \
  --size 2048 \
  --target-rank-coverage 0.95 \
  --out local-exploration.json
```

This produces the first 32-observation development-machine panel.

## Evidence boundary

GitHub-hosted thresholds remain excluded.

The local harness starts from all four q candidates and computes dominance from
local observations.

## Current execution dependency

The latest MVCA/LDC preflight before B497 still had:

`operator_binding_missing`

for the LDC config and no authority grant for this new calibration action.

No unrelated OpenPencil authority was consumed.

## Claim ceiling

**HOST_SCOPED_LOCAL_FRESH_PROCESS_EXPLORATION**

## Next

B498 should implement the host-bound local policy promoter.

The promoter must:

- require enough observations for the requested coverage;
- accept only locally observed Pareto q values;
- bind the policy to the exploration fingerprint;
- fail closed on insufficient n or fingerprint mismatch;
- emit the same generic Governor policy schema consumed by B494.
