# B496 — Local/LDC Adapter Bootstrap Contract v0.1

Status: **HOST-BOUND LOCAL CALIBRATION BOOTSTRAP**.

## 1. Goal

B494-B495 established a usable GitHub Actions application surface.

B496 defines how the same application contract can move onto a development
machine without pretending that GitHub-hosted calibration applies locally.

## 2. Hard separation from hosted thresholds

The local bootstrap explicitly forbids importing the GitHub-hosted peak
breakpoints.

It does not copy:

- 50,696,192 B
- 58,941,440 B
- 71,512,064 B

onto the local machine.

Those values are evidence about the hosted-runner population.

## 3. Restore the full q candidate set

B487 observed q1 as dominated by q2 on the hosted repaired frontier.

That does not establish local dominance.

Therefore the local bootstrap candidate set is:

`{q1,q2,q4,q7}`.

q1 may only be removed after local measurements rebuild the local Pareto
frontier.

## 4. Host fingerprint

The bootstrap records a non-identifying environment fingerprint containing:

- operating system;
- kernel release;
- machine architecture;
- Python version;
- page size;
- CPU model;
- total visible memory;
- libc;
- cgroup-v2 presence.

It deliberately does not include hostname, username, home path, or network
identity.

A canonical SHA256 binds later local calibration to this environment description.

## 5. Initial local exploration

Frozen first stage:

- q={1,2,4,7}
- 8 fresh local processes per q
- 32 physical observations

Sample unit:

`fresh_local_process_on_bound_host`

Purpose:

- discover local q topology;
- estimate local runner/process variation;
- avoid importing hosted dominance.

## 6. Promotion target

For a 95% rank-max one-step target:

`n>=19`

per promoted local Pareto q.

Thus after the first 8 samples:

`+11`

fresh local process samples are required for every q that survives onto the
local Pareto frontier.

The final count depends on the locally observed Pareto set.

## 7. Coverage claim

Any later local coverage statement is conditional on:

- the same fingerprint-bound host;
- comparable runtime/software state;
- exchangeability of the fresh-process observations.

It is not a cross-host guarantee.

## 8. Shared application contract

The local adapter will reuse B494/B495 schemas:

Request:

- peak_budget_bytes
- minimum_rank_coverage

Decision:

`finite-ram-lab.governor-decision-receipt/v0.1`

Execution:

`finite-ram-lab.application-execution-receipt/v0.1`

Only the calibration population and environment binding change.

## 9. Fail-closed rules

The local adapter must refuse selection when:

- no local policy has been promoted;
- the current environment fingerprint does not match the policy binding;
- requested coverage exceeds available local evidence.

## 10. Next

B497 should execute the bootstrap through the approved local path:

`MVCA -> LDC -> development machine`

and collect the local environment fingerprint plus the first exploration panel.

No Remote Desktop Commander path is required or permitted for this lane.
