# B412 — B404 Physical Protocol Smoke PASS

## Status

B404 COMPLETE / PHYSICAL PASS.

## Valid run

- run: 36642946787
- launch commit: c6c0feb8db7d6314dddddf9b15d2c7ab5f1d19aa
- standard public-repo GitHub-hosted ubuntu-26.04 runner
- no larger paid runner
- no local-PC execution

## Frozen result

Normal lane:

- 12/12 SUCCESS
- b62 4/4
- b63 4/4
- b64 4/4
- TARGET_FAIL 0
- instrumentation hold 0
- normal re-primes 0

Sentinel:

- PASS
- epoch0 forced UNEXPECTED_REFILL
- invalidation prevented commit
- hard re-prime
- fresh epoch1 direct Q64
- final SUCCESS

Aggregate:

- protocol_smoke_pass=true
- reprimes_total=1
- invalidation_counts={UNEXPECTED_REFILL:1}

## Evidence

- analysis/inputs/B404-R2-PHYSICAL-RESULT-v1.json
- docs/B404-R2-TRANSACTIONAL-SPAWN-PHYSICAL-PASS.md
- raw manifest files=63
- raw content-set SHA=d5c819b4b7d413faa6f635fc9062f0941ee570afebbb149d5d8c1f33d05127cf
- aggregate artifact ID=11067486294
- artifact digest=sha256:2a6b9d5fd0af968e89d8ceaca90b468ebd745641b40178ac9f50d09e73ce4e37

## R1 retained separately

R1 run 36642120375 remains frozen as:

- 10/12 normal SUCCESS
- 1 TRACE_GAP hold
- 1 ABORTED
- TARGET_FAIL 0
- sentinel PASS
- observer v1 drain classification falsified

Do not rewrite R1 as success.

## Next

Implement and physically run B405 causal perturbation matrix:

- CLEAN
- RELEASE_ONLY
- UNEXPECTED_REFILL
- PTE_GROWTH

Do not open age-decoupling Stage A until B405 passes.
