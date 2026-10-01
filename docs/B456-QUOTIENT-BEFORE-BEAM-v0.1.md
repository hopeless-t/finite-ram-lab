# B456 — Quotient Before Pareto Beam v0.1

Status: **synthetic beam benchmark with one fixed mixed-controller check**. No physical experiment ran.

## 1. Question

B455 proved that safety-aware local quotienting preserves the exact distinct Pareto objective-vector frontier.

B456 asks a different question:

> Does quotienting also make the approximate B435 beam controller more effective at a fixed beam width?

The answer is workload-dependent.

## 2. Fixed B436 + B447 mixed scenario

The fixed mixed scenario has:

- raw combinations = 640
- quotient combinations = 384
- combination reduction = 40%
- exact frontier vectors = 240.

Beam widths tested:

- 4
- 8
- 16
- 32
- 64
- 96.

At every tested width, raw and quotient pipelines recover exactly the same fraction of the exact frontier.

Examples:

- width 4 -> 1.67%
- width 16 -> 6.67%
- width 64 -> 26.67%
- width 96 -> 40%.

Thus:

**fewer combinations do not imply better beam coverage.**

The B435 prefix Pareto prune already removes much of the local redundancy before scalar beam truncation in this scenario.

## 3. Synthetic redundancy panel

To test the regime where local quotienting should matter, B456 freezes a deterministic 200-case panel.

Each of three groups contains:

- 2 or 3 random base choices;
- one exact duplicate of a base choice;
- one locally dominated choice.

Seed:

45602.

Combination reduction:

- mean 84.59%
- minimum 78.4%
- maximum 93.75%.

## 4. Beam coverage result

### Width 4

- raw mean coverage = 34.41%
- quotient mean coverage = 34.41%
- improved cases = 0/200
- worse cases = 0/200.

The beam is too narrow for the quotient to help after the objective-extreme preservation step consumes the available width.

### Width 8

- raw = 54.22%
- quotient = 67.05%
- quotient better = 159/200
- quotient worse = 0/200.

### Width 16

- raw = 66.68%
- quotient = 95.20%
- quotient better = 182/200
- quotient worse = 0/200.

### Width 32

- raw = 87.40%
- quotient = 100%
- quotient better = 114/200
- quotient worse = 0/200.

### Width 64

- raw = 100%
- quotient = 100%.

## 5. Effective beam-width reduction

In this frozen panel, mean exact-frontier coverage >=90% requires:

- raw pipeline: beam width 64
- quotient pipeline: beam width 16.

Observed width reduction factor:

**4x.**

This is an empirical result for this panel, not a universal bound.

## 6. Why quotienting helps here

B435 performs lossless partial Pareto pruning after each group.

However exact duplicate plan identities are not strict-dominance duplicates.

They can survive as separate partial plans with the same objective vector.

A finite beam tracks plan identities, not only distinct objective vectors.

Therefore plan multiplicity can consume beam slots without increasing objective-space coverage.

B455 quotienting removes that multiplicity before beam search.

The result is more beam capacity available for distinct frontier directions.

## 7. Why the fixed mixed scenario does not improve

In the B436+B447 fixed scenario, the options removed by the quotient compiler do not create enough surviving redundant prefix multiplicity to affect which distinct objective points fit in the beam.

So:

- exact search becomes smaller;
- beam quality remains unchanged.

This separates two benefits.

### Enumeration benefit

Reduce total Cartesian combinations.

### Beam-diversity benefit

Reduce redundant surviving partial identities that compete for a finite beam.

A workload can have one without the other.

## 8. Scale caveat

B435 computes normalization scales from the supplied option groups.

Quotienting can therefore alter those scales as well as option multiplicity.

B456 deliberately does **not** claim that quotienting can never hurt beam coverage.

A separate exploratory scale-polluter probe found no regression in its bounded sample, but that result is not promoted here because it is not yet a theorem or a sufficiently broad benchmark.

The frozen claim remains:

> quotienting materially improves beam coverage in the frozen redundancy panel and is neutral in the fixed mixed scenario.

## 9. Software qualification

Isolated research-lane qualification:

- 3 tests
- 3 PASS
- runtime 4.316 s
- stderr SHA-256: sha256:33f9c7ecd288307c749b17f9c661a2c4300103b56c56455984185c43c9072d13.

Frozen 200-case panel output:

- SHA-256: sha256:395bee2f83fa2aef1a40e20d164b6a703740a892b956ae5e2cf299fcf9b30c.

Additional width-64 panel output:

- SHA-256: sha256:2951770072c1c3c8ec33fb62c8bde4fb22c142662ee241b78fb634ddfdd1f907.

No network calls or physical workloads were used by the benchmark.

## 10. New hypothesis H456 — Decision Multiplicity Tax

> Approximate search pays not only for the number of distinct objective states, but also for multiplicity of physically distinct plans that occupy the same or locally redundant decision states.

B454/B455 remove this tax before bounded search.

## 11. Next direction

B457 should make the beam itself quotient-aware.

Instead of relying only on compile-time pruning, the beam can:

1. canonicalize identical partial objective vectors at every prefix depth;
2. retain provenance sets for tied partial plans;
3. compute normalization scales from a quotient-invariant reference;
4. measure whether this eliminates sensitivity to duplicate plan multiplicity.

That would turn the empirical B456 gain into an algorithmic invariant rather than a preprocessing accident.
