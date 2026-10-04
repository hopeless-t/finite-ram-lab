# FR-FP-056 Receipt

Status: **PASS / TYPED HOSTED PHYSICAL RESIDENT-SERVICE-ACTUATION PARETO FRONTIER QUALIFIED**

Parent: **FR-FP-055**

Qualification:
- workflow run: 37224815026
- job: 111502177512
- execution head: 94c99602bcbf9a294f4b685fca055561da7c9605
- physical anchors: 4
- scalar_gain: null

Typed axes:
- resident byte-time: MiB-round, minimize
- semantic service cost: ms, minimize
- physical actuation cost: ms, minimize

All four hosted physical anchors are Pareto non-dominated.

Physical anchors:

- RENT_0
  - resident: 4720 MiB-round
  - service: 556.770 ms
  - actuation: 92.918 ms

- RENT_0_10
  - resident: 3400 MiB-round
  - service: 726.527 ms
  - actuation: 20.183 ms

- RENT_0_25
  - resident: 480 MiB-round
  - service: 1255.125 ms
  - actuation: 19.070 ms

- RENT_0_40
  - resident: 0 MiB-round
  - service: 1411.978 ms
  - actuation: 0.002 ms

Adjacent tested-anchor crossovers under an explicitly supplied memory rent:

- RENT_0 -> RENT_0_10: 0.073502 ms/MiB-round
- RENT_0_10 -> RENT_0_25: 0.180645 ms/MiB-round
- RENT_0_25 -> RENT_0_40: 0.287054 ms/MiB-round

Decision:

**EXPOSE_THE_PHYSICAL_RESIDENT_SERVICE_ACTUATION_FRONTIER_AND_REQUIRE_AN_EXPLICIT_MEMORY_RENT_BEFORE_SCALAR_POLICY_SELECTION**

Boundary:

These crossovers select only among the four physically tested anchors. They do
not establish that untested intermediate policies cannot be superior.

Next:

Only acquire additional physical policy points when the added resolution can
change a real external-rent decision.

Claim ceiling:

**FOUR_ANCHOR_HOSTED_PHYSICAL_PARETO_AND_CANDIDATE_CROSSOVERS_ONLY**
