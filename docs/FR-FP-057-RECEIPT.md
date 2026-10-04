# FR-FP-057 Receipt

Status: **PASS / DECISION-DIRECTED COMPLETE HOSTED PHYSICAL POLICY-PATH COVERAGE QUALIFIED**

Parent: **FR-FP-056**

Qualification:
- workflow run: 37226269361
- job: 111506446809
- execution head: 9909fb9defa1b4068ed860f803ccb9c21d87d642
- FP054 rent points: 12
- unique placement paths after semantic deduplication: 8
- existing physical paths: 4
- new physical paths measured: 4

## Deduplicated physical acquisition

New representative rents:
- 0.075
- 0.15
- 0.20
- 0.30

Equivalent rent values were not measured twice.

All four new paths physically matched the shadow target residency.

## Complete physical path set

P0
- resident: 4720 MiB-round
- service: 556.770 ms
- actuation: 92.918 ms

P1
- resident: 4240
- service: 611.889
- actuation: 79.820

P2
- resident: 3400
- service: 726.527
- actuation: 20.183

P3
- resident: 2720
- service: 831.116
- actuation: 23.401

P4
- resident: 2400
- service: 888.211
- actuation: 25.443

P5
- resident: 480
- service: 1255.125
- actuation: 19.070

P6
- resident: 320
- service: 1297.515
- actuation: 10.522

P7
- resident: 0
- service: 1411.978
- actuation: 0.002

All eight paths are typed Pareto non-dominated.

## Exact scalar lower envelope with explicit memory rent

- P0: [0, 0.073502)
- P2: [0.073502, 0.158539)
- P3: [0.158539, 0.184802)
- P4: [0.184802, 0.187782)
- P5: [0.187782, 0.211520)
- P6: [0.211520, 0.324820)
- P7: [0.324820, +infinity)

New physical paths entering the scalar lower envelope:
- P3
- P4
- P6

P1 remains typed Pareto non-dominated but is unsupported by the one-dimensional
memory-rent scalarization.

Therefore:
- keep P1 in the typed Pareto evidence surface;
- do not keep P1 in the hot scalar-rent lookup.

Decision:

**PHYSICALLY_MEASURE_EACH_DECISION_DISTINCT_POLICY_PATH_ONCE_AND_COMPILE_ONLY_SCALAR_SUPPORTED_PATHS_INTO_THE_HOT_RENT_LOOKUP**

Meta consequence:

Experiment acquisition is itself residency-managed:
- deduplicate semantically identical policies before physical measurement;
- after qualification, keep only decision-supported paths in the hot lookup;
- retain unsupported Pareto evidence in cold typed storage for other policy
  surfaces.

Claim ceiling:

**EIGHT_UNIQUE_HOSTED_PHYSICAL_POLICY_PATHS_FROM_THE_FP054_TWELVE_POINT_RENT_SWEEP_ONLY**
