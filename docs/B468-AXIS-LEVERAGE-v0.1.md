# B468 — Axis Leverage Analysis v0.1

Status: **OFFLINE AXIS-SELECTION ANALYSIS / PROPOSAL ONLY**.

## 1. Question

The dogfood application can now perturb conditions and learn across runs.

The next problem is not "what value should this knob use?"

It is:

> **Which knob is worth spending experiments on?**

B468 compares the measured effect scale of the two currently explored axes.

## 2. Frozen source effects

### Representation / residency schedule — B463

Streamed fold versus all-resident:

- median absolute peak effect ~= 25,155,584 B;
- exact semantics preserved;
- median latency ratio ~= 1.05799.

### Tile granularity — B465/B467

64 -> 32:

- median absolute peak effect = 2,048 B;
- median latency ratio ~= 1.01584.

64 -> 128:

- median absolute peak effect = 36,864 B;
- median latency ratio ~= 0.99219.

The largest median tile-row peak effect observed is 36,864 B.

## 3. Peak leverage ratio

Define a simple experimental leverage ratio:

```text
L_peak =
|representation median peak effect|
/
max(|tested tile median peak effects|)
```

For the frozen specimens:

```text
L_peak ~= 25,155,584 / 36,864
       ~= 682
```

This is not a universal physical constant.

It is an experiment-prioritization observation for the current workload.

## 4. Decision

For peak-memory research:

`tile_rows`

is deprioritized.

The next proposed axis is:

`resident_lane_concurrency_q`.

Interpretation:

- q=1: stream/fold one residue lane at a time;
- q=7: retain all seven residue lanes before folding;
- q=2 or q=4: grouped streaming between those extremes.

This is the most direct interpolation between the two representation schedules
that produced the large B463 effect.

## 5. Coarse sweep

Frozen proposal:

```text
q in {1,2,4,7}
```

Hold constant:

- total residue lane count = 7;
- tile_rows = 64;
- numerical workload;
- input seed/value range;
- exactness gate.

Measure:

- normalized peak growth;
- work latency;
- exact semantic equality.

## 6. Why this connects the research threads

The q axis is simultaneously:

- a Finite RAM residency variable;
- an Ozaki/CRT representation-scheduling variable;
- a KMEP-style operating-point variable;
- a future governor control knob.

It asks the useful question:

> How much concurrency should be resident simultaneously before the latency gain
> stops paying for the memory cost?

## 7. Claim ceiling

**OFFLINE_AXIS_LEVERAGE_ANALYSIS**

B468 does not execute q.

It does not prove the q frontier is monotonic.

It only establishes that the current evidence justifies spending the next bounded
experiment budget on q rather than more tile-row tuning.

## 8. Next

B469 should implement grouped residue production/folding and execute the frozen
coarse sweep q={1,2,4,7}.
