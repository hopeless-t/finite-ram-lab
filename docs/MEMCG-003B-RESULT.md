# MEMCG-003B Non-Consuming Seven-Slot Result v1

> **Status:** PASS / REJECT_K7_SLOT_MODEL_B / RIGHT-CENSORED PASSIVE THRESHOLD
> **Run:** `36527502073`
> **Launch commit:** `5987143f7aaced18165289c76969b6ff386895db`
> **Aggregate artifact id:** `11015282127`
> **Artifact digest:** `sha256:4d3bec13e22c8136701546858046e48716ca36cc007689967d8a4d6c27ff8525`

## Preregistered decision

`REJECT_K7_SLOT_MODEL_B`

Support blocks:

`0 / 4`

Passive DISTINCT_CHURN thresholds:

`[null, null, null, null]`

No target `memory.current` drop >=16 pages was observed through eight distinct challenger insertions in any block.

## Important censoring interpretation

The analyzer reports:
- best K by absolute error = 9
- best K by MDL = 9
- posterior mode K = 9

These values **do not mean that K=9 was observed**.

The experiment only challenged through m=8. Every threshold is right-censored beyond the observed range.

K=9 and K=10 tie exactly:
- total absolute error: 0
- MDL: 4.9820780920 bits
- posterior mass: 0.4999975309 each

The implementation breaks the K=9/K=10 tie by choosing the smaller integer.

Therefore the accepted scientific statement is:

**no passive >=16-page eviction threshold was observed for K <= 8.**

Not:

**the cache capacity is 9.**

## Final recharge result

After the passive sequence, target was touched exactly once.

DISTINCT_CHURN final recharge:
- block0: 0 pages
- block1: +64 pages
- block2: +64 pages
- block3: +64 pages

Thus in 3/4 blocks, target had no consumable local stock at final probe despite no large passive `memory.current` drop having been observed during the challenger sequence.

This falsifies the simple observable model:

**target-stock eviction -> contemporaneous >=16-page drop in target memory.current.**

## Controls

NO_CHURN:
- no passive >=16-page drops in 4/4 blocks.

SIX_ONLY:
- no passive >=16-page drops in 4/4 blocks.

SAME_MEMCG_ACTIVITY:
- block0: 65-page drop at m=1
- block1: no large drop
- block2: 63-page drop at m=1
- block3: 62-page drop at m=1

Important implementation detail:

the SAME_MEMCG_ACTIVITY arm creates one new persistent competitor memcg before its repeated same-memcg touches begin.

Therefore the m=1 event is compatible with an effect from that **initial distinct competitor insertion** or its associated startup activity. It is not evidence that repeated activity in an already-existing memcg alone causes the target drop.

## Small subthreshold motion

DISTINCT_CHURN:
- block2: 1-page drop at m=2
- block3: 3-page drop at m=3

SIX_ONLY:
- block0: 3-page drop at m=2

These remain below the preregistered 16-page threshold and are preserved as observations, not promoted to eviction events.

## Accepted conclusion

MEMCG-003B cleanly rejects the preregistered passive-drop K7 observable model.

The source-level fact `NR_MEMCG_STOCK=7` remains true for the inspected Linux source, but this experiment shows that its slot replacement is **not directly mapped to a simple >=16-page step in target cgroup memory.current within eight challengers** under the tested hosted substrate.

The final +64 recharge in 3/4 DISTINCT_CHURN blocks establishes an important asymmetry:

**stock absence can be visible on subsequent demand even when no large passive target-current drop was seen beforehand.**

The next mechanism study should therefore focus on **controlled stock priming and direct state calibration**, not merely more challenger counts.

## Measurement lesson

MEMCG-003 exposed destructive observation.

MEMCG-003B removed destructive observation and exposed a second issue:

**the observable proxy itself is incomplete.**

This is a stronger result than simply increasing the challenger horizon.

## MATH-002 boundary

The primary result is frozen before any geometric secondary analysis.

MATH-002 may describe:
- response/control hull geometry;
- absence of a K7 outer-hull transition;
- seeded permutation structure.

It cannot revise this primary result.

## Authority boundary

Hosted Linux accounting research only.
Not a DRAM hardware law.
No local-PC execution.
No memory-control policy.
