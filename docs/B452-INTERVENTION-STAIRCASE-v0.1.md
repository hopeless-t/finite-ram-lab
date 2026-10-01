# B452 — Intervention Staircase Frontier v0.1

Status: **analytic digital-twin result**. No physical experiment ran.

## 1. Why advice_calls changes the geometry

B449 introduced `advice_calls` as a PRIMARY intervention-cost coordinate so the release-cadence frontier does not rely on noisy hosted timing.

For a fixed 96 MiB cold-file span, the natural intervention count is:

**N(K) = ceil(96 / K)**

for release cadence K.

For the frozen candidate set:

- K=32 -> 3 calls
- K=48 -> 2 calls
- K=64 -> 2 calls
- K=80 -> 2 calls
- K=96 -> 1 call.

This creates an intervention staircase.

## 2. Memory/pressure model

Reuse the B445 digital-twin form:

**P(K,H) = min(B + K, H)**

with:

- B = 78.609 MiB
- pressure when B + K > H.

Clean ephemeral excess differs from peak only by the same clean-floor proxy, so it has the same ordering in K.

The modeled PRIMARY vector is:

(peak, ephemeral excess, pressure, pgscan proxy, advice calls).

## 3. Why 64 and 80 are dominated

K=48, 64, and 80 all require two advice calls.

Within that equal-intervention class:

- peak demand is nondecreasing in K;
- ephemeral excess is nondecreasing;
- pressure cannot improve as K increases.

Therefore 48 is never worse than 64 or 80 on the modeled PRIMARY coordinates and is strictly better whenever their memory/pressure state differs.

So 64 and 80 are not expected frontier arms.

They remain valuable mechanism arms.

## 4. Capacity creates a staircase of strategy regimes

The important thresholds are not all five B+K values.

For Pareto topology, only the smallest cadence in each relevant intervention class matters.

### Threshold 1

B + 32 = **110.609 MiB**

Below this capacity, every tested cadence is capacity-clamped and pressured.

Their memory/pressure coordinates collapse together, so the arm with the fewest interventions wins:

**frontier = {96}.**

### Threshold 2

B + 48 = **126.609 MiB**

Between 110.609 and 126.609 MiB:

- 32 is pressure-free and memory-light;
- 96 still minimizes intervention count.

So:

**frontier = {32,96}.**

At and above 126.609 MiB:

- 48 becomes the minimum-memory two-call tradeoff;
- 32 remains the three-call memory minimum;
- 96 remains the one-call intervention minimum.

So:

**frontier = {32,48,96}.**

## 5. Why the B447 planned capacities have constant topology

The planned capacities are:

- 144 MiB
- 160 MiB
- 176 MiB.

All are above:

126.609 MiB.

Therefore the B449 expectation:

{32,48,96}

at all three capacity points is not merely a numerical coincidence.

It follows analytically from the intervention staircase.

## 6. What capacity still changes above 126.609

Even though frontier membership is predicted to remain constant, objective values still move.

In particular:

- 96 transitions from pressured to pressure-free only at its own intrinsic threshold;
- 80 provides threshold-localization evidence;
- peak and reclaim coordinates can change with H;
- measured dynamic costs may violate the static twin.

So B447 remains informative.

Its expected null result is:

**same frontier identities, changing objective vectors.**

## 7. New distinction

B452 separates two types of capacity threshold.

### Topology-activation threshold

A new intervention tradeoff arm joins the Pareto frontier.

For the frozen model:

- 110.609 MiB activates 32
- 126.609 MiB activates 48.

### Mechanism threshold

A dominated arm changes pressure/reclaim behavior without joining the Pareto frontier.

Examples:

- 64
- 80
- later 96 pressure transition.

This sharpens the B449 principle:

**Pareto irrelevance is not mechanism irrelevance.**

## 8. Validation

The closed-form three-regime result was compared against brute-force Pareto evaluation over the full five-cadence model.

Deterministic validation:

- 10,000 random MemoryHigh values
- range just above the clean-floor proxy through 240 MiB
- closed form equals brute-force frontier in every case.

## 9. New hypothesis H452 — Intervention-Class Compression

> When several plans have the same intervention count and every physical pressure/memory objective is monotone in their frontier width, only the smallest-width plan in that intervention class can contribute a distinct Pareto tradeoff.

This can reduce controller search space before physical evaluation.

It is analogous to B435 partial Pareto pruning, but derived from intervention semantics rather than observed objective values.

## 10. Next direction

B453 should generalize this into a symbolic **cadence frontier compiler**.

Input:

- file/span size F;
- candidate cadences K;
- intrinsic-base estimate B;
- intervention-cost function N(K);
- monotone memory/pressure assumptions.

Output:

- equivalence classes by intervention count;
- dominated mechanism-only cadences;
- topology-activation thresholds;
- frontier regimes as a function of capacity.

Then compare the symbolic compiler with B434 exact enumeration on randomized discrete cadence systems.
