# B497 — Local Calibration Exploration Harness v0.1

Status: **EXECUTABLE HOST-BOUND EXPLORATION HARNESS**.

## 1. Goal

B496 defined the local calibration contract.

B497 packages the full initial exploration into one command that can later be
invoked through the approved MVCA -> LDC path.

## 2. Command

With the analysis/runtime dependencies installed:

```bash
frl local-calibrate \
  --samples-per-q 8 \
  --size 2048 \
  --target-rank-coverage 0.95 \
  --out local-exploration.json
```

Default full exploration:

- q={1,2,4,7}
- 8 fresh child processes per q
- 32 physical observations
- repaired TILED_WHERE implementation
- seed469 workload

## 3. Order balance

The eight q orders are frozen so each q occupies every execution position twice.

This controls simple within-panel order effects while preserving fresh child
processes as the local sample unit.

## 4. Host binding

The harness records the local host fingerprint before the panel and again after
the panel.

If the canonical fingerprint SHA changes, the entire panel fails closed.

The fingerprint intentionally excludes user/host/network identity.

## 5. Semantic gate

Every child must be exact.

All q observations must produce one common output digest for the deterministic
workload.

A digest mismatch blocks resource interpretation.

## 6. Local frontier

For each q B497 computes:

- sample count;
- median normalized peak;
- empirical maximum peak;
- median work latency;
- current rank-max coverage floor.

It then computes the local two-objective memory/latency Pareto set.

There is no hard-coded q1 exclusion.

## 7. Promotion remains separate

At the default n=8 exploration:

`coverage floor = 8/9 ~=88.889%`

so the harness does not promote a production local policy.

For every q on the locally observed Pareto frontier, the 95% target still
requires:

`n=19`

or +11 fresh-process observations after the initial panel.

## 8. Hosted harness smoke vs development-machine evidence

B497 CI may run a small panel on a GitHub-hosted runner to prove the harness is
executable.

That smoke result is not development-machine calibration.

Only an execution through the approved local path on the target machine may
become local policy evidence.

## 9. LDC handoff

Current approved execution path remains:

`Web ChatGPT -> MVCA -> LDC -> local machine`

No Remote Desktop Commander path is used.

Once an appropriate B497-specific bounded action is admitted, the local side only
needs to:

1. enter the finite-ram-lab checkout;
2. install/verify the analysis runtime;
3. execute the frozen `frl local-calibrate` command;
4. return the JSON result and its SHA256.

## 10. Claim ceiling

**HOST_SCOPED_LOCAL_FRESH_PROCESS_EXPLORATION**

## 11. Next

After a real development-machine B497 panel exists:

- freeze its host fingerprint and raw q observations;
- identify the local Pareto q set;
- spend +11 observations on each local Pareto q;
- build the first host-bound local Governor policy.
