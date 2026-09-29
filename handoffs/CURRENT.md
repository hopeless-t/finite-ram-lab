# CURRENT

> Latest bounce: B392
> Stage: 17-PAGE LATENT COMPONENT / OBS-001 TRACE GATE PASS
> Stop: READY FOR FRESH OBS-001 DIAGNOSTIC RELAUNCH

## Existing-evidence discovery

MATH-015:
docs/MATH-015-17-PAGE-LATENT-COMPONENT.md

Controlled-spawn v2 raw:
- exact -17 events: 20
- other negatives: -13, -3, -2

Start-state modes:
- 98..100
- 114..117
- 161..163
- 179..180

Descriptive additive lattice:
baseline + optional 17 + optional ~63

Fit:
- exact 68/72
- within 1 page 69/72

Exact -17 shifted by -17:
- exact clean-support landing 17/20
- within 1 page 19/20

Near-lattice association:
- no-17 component: 0/42 exact -17
- 17-component: 19/27 exact -17
- one-sided Fisher ~4.8e-11
- post-hoc descriptive only

Working hypothesis:
a transient 17-page accounted component can disappear asynchronously.

Identity unresolved:
- Prep-CPU stock drain is a strong candidate
- ordinary/other uncharge remains possible

## OBS-001

Design:
docs/OBS-001-CHARGE-UNCHARGE-DISCRIMINATOR.md

Frozen diagnostic scale:
- 4 blocks
- 12 identities/block
- 24 touches/identity
- 48 identities
- 1152 touches
- no b63 reliability claim

## Trace capability

Final gate:
run 36614225845 = PASS

Probeable:
- drain_stock
- refill_stock
- try_charge_memcg
- page_counter_uncharge

Not directly probeable:
- uncharge_batch

Also PASS:
- page_counter_uncharge nr_pages==17 filter
- stacktrace trigger
- trace buffer control
- root trace_marker write/readback
- cleanup readback

## Infrastructure findings

OBS-001 development exposed and repaired:
- runner-user vs sudo tracefs capability confusion
- escaped GitHub workflow expressions
- trace_marker permission mismatch
- cleanup set +e false-success bug
- cleanup return-code false-failure bug
- root observer / runner-UID worker separation

No prior OBS-001 scientific attempt is valid.
Do not interpret their job labels as data.

## Next action

Fresh OBS-001 diagnostic relaunch only.

Goal:
directly classify the caller of -17.

No reliability scaling before observer cleanliness is resolved.

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
