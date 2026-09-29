# B392 — 17-page latent component + OBS-001 trace gate

## Status

EXISTING-EVIDENCE DISCOVERY COMPLETE.
TRACE EXECUTION CAPABILITY = PASS.
NO VALID OBS-001 SCIENTIFIC DIAGNOSTIC RUN YET.

## MATH-015 result

Controlled-spawn v2 raw sequences were re-opened across all 8 blocks.

Negative measured deltas:
- -17 pages: 20
- -13 pages: 1
- -3 pages: 1
- -2 pages: 1

Start-state modes are concentrated around:
- 98..100
- 114..117
- 161..163
- 179..180

An additive descriptive lattice:
- baseline
- baseline + 17
- baseline + ~63
- baseline + 17 + ~63

fits:
- 68/72 exactly
- 69/72 within 1 page

Among exact -17 specimens:
- subtracting 17 lands exactly on clean support: 17/20
- within 1 page of clean support: 19/20

Pseudo-holdout:
- blocks 0..3: 33/36 exact
- blocks 4..7: 35/36 exact

Within the 69 near-lattice trials:
- no-17 class: 0/42 exact -17
- 17-component class: 19/27 exact -17
- one-sided Fisher p ~ 4.8e-11

This is post-hoc descriptive evidence, not a preregistered confirmatory p-value.

Strong working hypothesis:
a reproducible transient 17-page accounted component exists at trial start and can later disappear asynchronously without shifting the stock-CPU terminal phase.

Preparation-CPU memcg stock is a concrete candidate but is not yet proven.

## Source audit

Linux v7.0 has at least two relevant uncharge families:

1. drain_stock() -> memcg_uncharge(...)
2. uncharge_folio() -> uncharge_batch() -> memcg_uncharge(...)

Therefore memory.current == -17 alone cannot identify the caller.

FOLIO_BATCH_SIZE is 31, so a generic fixed 17-page folio batch explanation is unsupported.

## OBS-001 instrumentation work

Added:
- docs/MATH-015-17-PAGE-LATENT-COMPONENT.md
- docs/OBS-001-CHARGE-UNCHARGE-DISCRIMINATOR.md
- src/finite_ram_lab/obs001_uncharge_trace.py
- tests/test_obs001_uncharge_trace.py
- specs/OBS-001-17-PAGE-UNCHARGETRACE-v1.json
- trace workflows

### Capability history

v1:
- false HOLD due testing runner-user writability instead of sudo trace access

v2:
- kprobe capability PASS
- useful probe points:
  - drain_stock
  - refill_stock
  - try_charge_memcg
  - page_counter_uncharge

Scientific workflow attempt:
- invalid due escaped GitHub expressions before runner

Next attempt:
- observer trace_marker permission failure
- exposed a false-success bug: cleanup set +e leaked to parent shell

Fail-closed repair:
- cleanup moved to subshell
- worker UID separated from root observer

Next attempt:
- correctly failed
- exposed cleanup return-code bug

Cleanup repaired:
- idempotent cleanup now success-neutral

### Final execution gate

Run:
36614225845

Result:
PASS

Verified:
- drain_stock probeable
- refill_stock probeable
- try_charge_memcg probeable
- page_counter_uncharge probeable
- nr_pages == 17 event filter accepted
- stacktrace trigger accepted
- trace buffer control accepted
- root Python trace_marker write/readback accepted
- cleanup readback PASS

uncharge_batch is not directly probeable on this hosted kernel.

## Invalid scientific attempts

No OBS-001 scientific attempt to date is valid.

Reasons include:
- workflow syntax
- trace_marker permission
- fail-closed infrastructure bugs

Do not use their artifact/job success labels as scientific evidence.

## Next

Relaunch the frozen 4 x 12 x 24 OBS-001 diagnostic only after changing its marker to a fresh version.

Primary discriminator:
- -17 + coincident drain_stock/page_counter_uncharge(17) => STOCK_DRAIN
- -17 + page_counter_uncharge(17) without drain_stock => OTHER_UNCHARGE
- -17 without matching event => UNCORRELATED / observer issue

No b63 reliability scaling until this caller is resolved.
