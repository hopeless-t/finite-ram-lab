# Bounce Handoff

> **Bounce ID:** B170
> **Status:** COMPLETE / STRATA-001 PILOT AGGREGATE PATH FIX

## Pilot run reconciliation

Run `36336994450` concluded FAILURE, but all six experimental block jobs completed SUCCESS.

Only the aggregate job failed.

Ordinary CI for the launch commit also completed SUCCESS:

- run: `36336994503`
- conclusion: `success`

## Root cause

`actions/download-artifact` expanded block artifacts under directories named:

`strata001-pilot-block-<N>`

The collector only searched:

- `block-*`
- `strata001-block-*`

Therefore it raised:

`ValueError: no STRATA-001 pilot evidence found`

even though all six block artifacts were downloaded successfully.

## Fix

Collector now also recognizes:

`strata001-pilot-block-*`

and the block-name regex accepts that canonical downloaded-artifact directory form.

A regression test creates exactly that directory shape.

## Scientific boundary

No trial data, pilot contract, estimator, pressure level, arm, or scientific outcome changed.

The 36 physical trials should not be re-run merely because aggregation failed.

## Next action

Validate B170 with ordinary CI.

If PASS, recover the six existing block artifacts and aggregate them without re-running the physical pilot.

## Authority boundary

Pilot evidence recovery only.
