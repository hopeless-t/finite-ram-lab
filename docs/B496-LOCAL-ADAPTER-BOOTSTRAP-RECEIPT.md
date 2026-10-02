# B496 — Local/LDC Adapter Bootstrap Receipt

Status: **PASS / LOCAL BOOTSTRAP CONTRACT QUALIFIED**

## Frozen execution

- workflow run: 36965649853
- job: 110708711789
- execution head: 524bec11100c7df8527c6e46fabef713049812be
- tests: 4/4 PASS
- artifact ID: 11209199726
- artifact ZIP SHA256: 8f14f4b3676c21b46798366e0f98754c7ab156d9736722ccb3a738253f22ce47
- bootstrap plan SHA256: 83ad69dfd20d87d1df332e873a99a23f28f6a2fea7ab95e01c98478d380b66e0

## Local candidate set

`{q1,q2,q4,q7}`

q1 is restored for local exploration.

The hosted-runner q1 dominance result is not imported as a local fact.

## Hosted-threshold isolation

`hosted_threshold_import_allowed = false`

The local bootstrap plan contains none of the B493 hosted peak breakpoints.

## Initial exploration

- 8 fresh local process observations per q
- 4 q values
- 32 physical observations

Sample unit:

`fresh_local_process_on_bound_host`

## Promotion target

95% rank-max target:

- n=19 per locally promoted Pareto q
- +11 samples after the initial n=8 exploration for each promoted q

## Environment binding

The bootstrap captures a non-identifying host fingerprint and canonical SHA256.

Later local policy promotion must bind to that fingerprint and fail closed if the
environment no longer matches.

## Current LDC execution preflight

At the time of this receipt, the MVCA/LDC readback reported:

- MVCA status: CURRENT
- working tree: clean
- LDC config: UNKNOWN
- reason: operator_binding_missing
- authority_grant: NONE

The currently approved unconsumed MVCA action belongs to the OpenPencil S0 lane
and is unrelated to this experiment.

Therefore no local calibration execution was attempted through an unrelated
authority path.

## Claim ceiling

**HOST_SCOPED_LOCAL_CALIBRATION_BOOTSTRAP**

## Next

B497 should package the complete local exploration harness so that, once the
operator binding is restored and an appropriate bounded LDC action is admitted,
the 32-observation local panel can be executed without redesigning the
experiment.
