# CURRENT

> Latest bounce: B416
> Stage: SMALL_RESIDUAL_REFILL ESTABLISHED
> Stop: READY TO IMPLEMENT / LAUNCH R13-B2 REFILL1 PROVENANCE

## Chapter II frontier

Historical SUCCESS/FAIL has been decomposed into explicit state transitions.

Established named states/mechanisms:

- VERIFIED_DIRECT_Q64_RESET: measured one-page direct Q64 establishes verified residual R0=63.
- PREVERIFY_S64 / MAX_STOCK_BOUNDARY: natural pre-VERIFY S0=64.
- STARTUP_STOCK_SEED: startup Q64/refill63 can leave large inherited stock on the future stock CPU.
- SMALL_RESIDUAL_REFILL: systemd PID1 can return one page to the later measured owner memcg on the future stock CPU, yielding S0=1 and measured T=2.
- TARGET_STOCK_EVICTION: verified residual stock can be asynchronously drained before the next measured transition.
- RELEASE_ONLY: source-grounded shared-LRU release changes accounting without consuming the target residual.

No complete verified B405 target path has produced TARGET_FAIL.

## R13-A historical run and corrected replay

Physical run 36693262942 is frozen under its original semantics:

- 128 measured identities
- frozen discovery_pass=false
- frozen panel_coverage_pass=false
- frozen CLASSIC_REFILL63_LEAK=35
- frozen INVALID_OBSERVER=11
- frozen T1_NO_SMALL_REFILL=82
- frozen promoted count=0

Do not rewrite that aggregate.

A reducer-scope defect was found prospectively: owner matching scanned all earlier block events and could attach an earlier identity after a memcg-pointer reuse.

Corrected replay of the same raw evidence, bounded from current-trial STARTUP PRE to current boundary PRE:

- T1_NO_SMALL_REFILL=127
- SMALL_REFILL_EXPLAINS_DELAY=1
- CLASSIC_REFILL63_LEAK=0
- first-Q64 histogram: T1=127, T2=1

The unique delayed specimen remained trial 0:28:
- T=2 / inferred S0=1
- current-trial owner refill1 exactly once
- owner refill63 preboundary=0
- systemd PID1 on future stock CPU
- Q64 miss=0
- refill-spectrum miss=1

This replay strengthened the hypothesis but did not retroactively promote it.

Frozen replay:
- analysis/inputs/R13A-CORRECTED-REPLAY-v1.json

Prospective reducer fix:
- current-trial STARTUP PRE is the retrospective lower bound
- pointer reuse from earlier identities is rejected

## R13-B1 Stage 1 — mechanism establishment

Experiment:
TX-SMALL-RESIDUAL-REFILL1-CAPTURE-v1

Run:
36697763027

Design:
- 4 blocks x 8 = 32 fresh CPUSET_PREP_ONLY identities
- no automatic scale expansion
- refill_stock probe phase-gated
- premeasurement filter: nr_pages == 1 OR nr_pages == 63
- measured Q64/refill63 probes active only during each measured touch
- current-trial evidence only
- zero-miss required for promoted specimens

Aggregate:
- trial_count=32
- valid_trial_count=31
- T1_NO_OWNER_REFILL1=29
- SMALL_RESIDUAL_REFILL_ESTABLISHMENT=2
- INVALID_OBSERVER=1
- T histogram: T1=29, T2=2
- establishment_pass=true
- promoted trials: 1:4 and 2:7
- measured probe miss trials: none
- premeasure probe miss trials: 2:2 only

Both promoted specimens independently have:

- CPUSET_PREP_ONLY startup
- future stock CPU
- current-trial owner refill_stock(...,1) exactly once
- emitter systemd PID1
- no current-trial owner refill63 in premeasurement epoch
- first measured direct Q64 at T=2
- inferred S0=1
- premeasurement refill missed=0
- measured Q64/refill63 missed=0
- single-process cgroup
- clean PTE/CPU/worker/trace guards

Mechanism status:

SMALL_RESIDUAL_REFILL = ESTABLISHED_IN_TWO_ZERO_MISS_PHYSICAL_SPECIMENS

Frozen evidence:
- analysis/inputs/SMALL-RESIDUAL-REFILL1-CAPTURE-STAGE1-PHYSICAL-RESULT-v1.json
- docs/OBS-011-SMALL-RESIDUAL-REFILL-ESTABLISHED.md
- raw files=84
- bytes=3,263,807
- content-set SHA-256=927593f98e4d532ab045a563b206e98ffc454c85c2eff190c8481f06b7243f34
- aggregate artifact ID=11087599946
- aggregate digest=sha256:a0f7f3dea075b98f96c6aedf8f11555dc7d32b45d6cd6a14a75004b56cf7b51e

README now reflects the named state-transition frontier.

## R13-B2 next experiment — provenance only

Mechanism existence is closed enough for Chapter-II purposes.

The remaining question is narrower:

> Which kernel call path caused the systemd PID1 refill_stock(owner_memcg,1) receipts?

Candidate source-grounded provenance classes:

- OBJCG_UNCHARGE_REFILL1
- SOCKET_UNCHARGE_REFILL1
- TRY_CHARGE_EXCESS_REFILL1
- OTHER_REFILL1_CALLER

Recommended Stage 1:

- 4 blocks x 8 = 32 fresh CPUSET_PREP_ONLY identities
- no automatic scale expansion
- enable refill1 observer only during STARTUP window
- refill filter: nr_pages == 1
- conditional stacktrace on refill1 only
- disable immediately after STARTUP POST
- use phase-gated measured Q64 + target refill63 afterward to resolve owner_memcg and T
- provenance promotion requires:
  - T>1
  - owner refill1 on future stock CPU in current STARTUP
  - zero STARTUP refill1 probe misses
  - zero measured Q64/refill63 misses
  - stack captured and source-grounded

If no provenance specimen is captured in Stage 1, freeze the diagnostic and return to council. Do not automatically expand the sample.

After caller provenance is established, stop expanding pre-VERIFY taxonomy and return to the already-frozen TX-AGE-DECOUPLING design for verified-state hazards.

## Authority

R13-B2 physical continuation is authorized by the user.

Standard public-repository GitHub-hosted runner only.
No paid larger runner.
No local-PC execution.
No automatic scale expansion.
No reliability certification.
