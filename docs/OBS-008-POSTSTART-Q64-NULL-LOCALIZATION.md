# OBS-008 — Post-start migration interval contains no target Q64 seeding

> Run: 36688225173
> Launch commit: `a683fcbc0cb17175891b0022428c0e5a1952ea2f`
> Status: PHYSICAL PASS / LOCALIZATION NEGATIVE RESULT

## Result

`TX-PREMEASURE-Q64-CALLPATH-v1` observed 32 fresh worker identities.

- 32/32 `WITHIN_BOUND`
- bound violations: 0
- critical Q64 probe missed: 0 in every block
- single-process cgroup: 32/32
- explicit post-`_start()` migration-to-first-touch target Q64 events: **0/32**

The zero-event result held in both timing arms:

- settle 0 ms: 0 premeasurement Q64 events across 16 identities
- settle 5 ms: 0 premeasurement Q64 events across 16 identities

Despite that null interval, first measured Q64 boundaries still included high natural states:

```text
T=1   24
T=2    2
T=36   1
T=46   1
T=47   2
T=48   1
T=64   1
```

Therefore high pre-VERIFY stock does not require a new target Q64 after `_start()` returns.

## Timing-arm interpretation

Mean T:

- 0 ms: 13.5625
- 5 ms: 6.1875

Both medians were 1.

A 200,000-draw permutation Monte Carlo on the absolute mean difference gave an approximate two-sided tail probability of 0.291.

This panel therefore does not provide persuasive evidence that a 5 ms post-migration dwell itself changes T.

## Contrast with R9

R9 reported target-PID Q64 bursts before measured touch 1 for four high-T identities.

R9's premeasurement snapshot included the entire trace accumulated before the first measured touch, including `_start()` / transient service creation.

R10 deliberately bound the target-PID Q64 observer only after `_start()` returned.

The R10 null result therefore localizes the R9 burst candidate to an earlier interval:

```text
systemd transient service creation
  -> child/process startup
  -> worker READY / _start return
```

rather than the controlled:

```text
_start return
  -> explicit migration
  -> 0/5 ms settle
  -> first measured touch
```

## Important raw clue

Frozen R9 high-T specimens contain Q64 events whose trace task PID later becomes the worker MainPID, with the first event carrying `comm="systemd"` and later events occurring under the same PID/counter.

This is consistent with the transient service process charging its memcg before or around exec/affinity setup, but R9 did not carry call-path stacks or explicit startup phase markers.

Therefore the correct next experiment is phase localization, not a causal conclusion.

## Candidate transition

`STARTUP_STOCK_SEED` is reserved as a candidate name:

> target memcg stock on the future stock CPU is seeded during transient service/worker startup before controlled migration, leaving a natural pre-VERIFY residual.

The name is not promoted to established mechanism until a phase-marked startup experiment observes the target PID/counter event in the startup interval.

## Evidence

- raw manifest files: 80
- raw bytes: 396,980
- content-set SHA-256: `456f890a8071aef02e09674fd1316c768a540366edeedbb6bb278d5e1567fc0f`
- aggregate artifact: `11084727839`
- artifact digest: `sha256:fc719e6d8a1f8cc8f3a6ce873c13038bab99ad5efbf7326140f9ab6187f5a91d`
- machine result: `analysis/inputs/PREMEASURE-Q64-CALLPATH-R1-PHYSICAL-RESULT-v1.json`

## Next

Instrument startup phases before invoking `systemd-run`, record `sched_process_exec`, and retrospectively attribute Q64/refill/drain events to the final MainPID and future stock CPU.
