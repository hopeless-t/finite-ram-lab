# CURRENT

> **Latest bounce:** B226
> **Stage:** STRATA-005 / RECORDER PATH REPAIRED / CI PENDING

## REC-002

Canonical PASS: run `36427808785`, 16/16 valid trials, zero Recorder-induced MemoryHigh-event delta in all 8 paired blocks.

## STRATA-005

B225 implementation was read back before launch and a semantic mismatch was found: Recorder was declared in the spec but bypassed by the workflow.

B226 repaired the execution path.

Every trial now goes through the STRATA-005 wrapper and records:

- run_start
- 24 memory.current checkpoint samples
- run_end

Expected REC-001 record count: 26.

The wrapper also emits the trial JSON consumed by aggregation.

## Frozen design

- MemoryHigh: 144 / 176 MiB
- arms: buffered / 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 total trials
- MemoryMax: 320 MiB
- hot anon: 64 MiB
- cold file: 96 MiB
- read chunk: 4 MiB

## Next fresh-bounce action

Read B226 ordinary CI once.

- success -> explicit launch marker in a separate commit;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the failure and repair atomically.

## Operating policy

Research mainline continues; Recorder repair is triggered by concrete counterexamples.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
