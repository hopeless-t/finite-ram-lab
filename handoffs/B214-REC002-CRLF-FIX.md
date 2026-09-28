# Bounce Handoff

> **Bounce ID:** B214
> **Status:** COMPLETE / REC-002 INFRASTRUCTURE FAILURE ATOMIZED + FIXED

## Failed hosted run

Run `36419229167` completed with conclusion `failure`.

All 8 matrix blocks failed before workload measurement in the same step. Representative job `108917661605` reported:

`argument --mode: invalid choice: 'recorder_off\\r'`

## Atomized finding

The Python csv writer emitted platform-standard CRLF records. The Bash `read` consumer split on comma but retained the trailing carriage return in the final field. Therefore the mode token became `recorder_off\\r` or `recorder_on\\r`.

This is a workflow portability/interface bug, not recorder overhead evidence and not a memory-pressure result. No REC-002 trial reached the measured workload.

## Pseudo-Council convergence

- Measurement reviewer: reject run as evidence; zero valid trials.
- Portability reviewer: make the producer/consumer contract explicit rather than stripping bytes ad hoc in multiple consumers.
- Minimal-change reviewer: set CSV `lineterminator="\\n"` at the producer and add a byte-level regression test.
- Authority reviewer: fixing repository code is allowed; rerunning the failed experiment is a separate launch decision.

Consensus: producer-side LF normalization plus regression test. Do not blind-rerun run 36419229167.

## Change

`write_schedule()` now emits LF-only CSV and the test suite asserts that schedule bytes contain no carriage return.

## Next action

Read ordinary CI for this fix once. If successful, create a new explicit REC-002 relaunch marker in a separate bounce. If pending, checkpoint EXTERNAL_WAIT. If failed, inspect only.

## Authority boundary

Hosted research/repository work only. No local-PC execution. No STRATA-005 launch. No memory-control policy authorized.
