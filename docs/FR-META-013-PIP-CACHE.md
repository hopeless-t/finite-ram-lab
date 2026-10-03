# FR-META-013 — pip Cache Dogfood

Status: **NEGATIVE DOGFOOD RESULT / THEORY UPDATED**

Parent: **FR-META-012**

## Hypothesis

Recent dependency-install spans were about 15-20 seconds. The candidate enabled
the pip cache built into actions/setup-python@v7, keyed by pyproject.toml.

## First run

Implementation CI:

- cache lookup: MISS;
- Install: about 20.19 s;
- full CI: PASS;
- cache saved under the expected setup-python key.

A miss on the first run was expected.

## Critical follow-up

The PR validation used the same dependency file and reported the same cache key,
but setup-python again reported:

    pip cache is not found

Its Install span was about 19.04 s.

The receipt-push CI was correctly cancelled by FR-META-009 concurrency, so the
surviving PR run is the relevant same-head follow-up specimen.

## Failure biopsy

Configuration is not evidence of reuse.

In the current stacked-branch / pull-request topology, this dogfood did not
demonstrate a usable restore path. The job also paid cache-save work at the end.

Therefore the cache is not promoted as a loop-speed primitive.

The workflow cache lines are removed in v0.2.

## Compiled lesson

Before enabling a cache:

1. identify the exact producer and consumer ref topology;
2. prove the consumer can restore the producer's key;
3. measure the target step rather than assuming a hit;
4. include save/restore overhead in the cost;
5. promote only after repeated useful reuse.

## Decision

**DO_NOT_PROMOTE_PIP_CACHE_FOR_CURRENT_STACKED_PR_FLOW**

A future experiment may revisit dependency acceleration using a scope-proven
cache, a durable shared artifact, or a prebuilt environment/image.

## Claim ceiling

**NEGATIVE_CI_DEPENDENCY_CACHE_RESULT_ONLY**
