# FR-META-006 — ABA Hot-Test Memoization

Status: **DOGFOOD PERFORMANCE CANDIDATE**

Parent: **FR-META-005**

## Hotspot biopsy

A timestamp-gap profile of a recent full CI suite found 565 completed tests.
The largest completion gap was about 29.1 seconds for the FR-GFX observer A/B/A
panel. The next slowest test was about 6.1 seconds.

The ABA panel regenerates the same deterministic A1 and A2 segments for every
observer arm, and regenerates the null arm for the false-perturbation table.

## Optimization

Do not reduce episodes, frames, blocks, tails, or equivalence thresholds.

Memoize deterministic segment means keyed by episode, segment, observer
constant overhead, and observer tail overhead. Also memoize the complete
mean-effect pair for an arm.

The original compute graph performs twelve segment evaluations per episode.
The candidate needs five unique segment means per episode: A1, A2, null B,
light B, and heavy B.

At 8,192 episodes:

- baseline: 98,304 segment evaluations;
- candidate: 40,960 unique segment means;
- structural reduction: 58.33%.

## Scientific guard

The optimization changes only repeated deterministic computation.

Existing frozen FR-GFX-005 output equality tests remain untouched. If any
numeric result changes, the old test suite fails.

Monte Carlo is not added because there is no uncertain research decision here.

## Speed rule learned

Before reducing sample size, search for repeated deterministic subproblems,
duplicate calculations across arms, reusable sufficient statistics, and exact
memoization opportunities.

Only after exact compute reuse is exhausted should the research loop consider
trading statistical power for speed.

## Claim ceiling

**TEST_HARNESS_COMPUTE_OPTIMIZATION_ONLY**
