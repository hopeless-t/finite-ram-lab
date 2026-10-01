# B467 — First Cross-Run Feedback Execution v0.1

Status: **FULL MULTI-RUN FEEDBACK CYCLE / BOUNDED**.

## 1. Goal

B465 executed the first intentional dogfood probe.

B466 consumed that completed result later and emitted a proposal only.

B467 now binds the B466 proposal into a new immutable decision before executing
the next physical probe.

This closes the first complete cross-run feedback loop.

## 2. Provenance chain

The frozen chain is:

```text
B465 telemetry
SHA256:
3d02cd3269e21b14b2d7a7a6291a59308be106c7860af5013b647f4a7512f92f
        |
        v
B466 offline proposal
SHA256:
64672a290dc46e40f5db021baeb9e02b86303da61100d0bc2fc90d6f8b97463f
        |
        v
B467 frozen decision
        |
        v
B467 bounded executor
        |
        v
new telemetry
```

Every edge is explicit.

## 3. Proposal binding

B467 refuses the B466 proposal unless its SHA256 matches the frozen value.

The proposal must also remain:

- PROPOSAL_ONLY;
- execute_now=false;
- requires_new_frozen_decision=true;
- action=PROBE_OPPOSITE_TILE_DIRECTION;
- changed variable exactly tile_rows 64 -> 128;
- strategy and lane_count held constant.

Only after those checks does B467 create a new runtime decision.

## 4. New decision

The B467 decision declares:

- mode = PROBE;
- partition = EXPERIMENTAL_INTERVENTION;
- baseline = streamed_7_t64;
- selected = streamed_7_t128;
- changed variable = tile_rows 64 -> 128;
- lane_count=7 held;
- strategy=STREAMED_FOLD held;
- source proposal SHA256;
- source B465 telemetry SHA256.

The decision is serialized, hashed, and then referenced by a new execution
contract.

The executor verifies that decision digest before any numerical work.

## 5. Physical execution

The executor reuses the qualified B465 surface.

Four matched fresh-process pairs are run with alternating order.

Hard semantic equality remains mandatory.

Observed telemetry is written to a new artifact.

No model update occurs inside the physical run.

## 6. Why this is the milestone

The application can now perform:

```text
useful/real workload
-> frozen intervention
-> telemetry
-> later analysis
-> bounded next proposal
-> new frozen decision
-> next intervention
```

without collapsing those phases into one adaptive opaque process.

That makes the runtime suitable for both:

- optimization research;
- intentional condition control / system identification.

## 7. Claim ceiling

**BOUNDED_CROSS_RUN_FEEDBACK_EXECUTION**

This is still one narrow tile-size family on a hosted numerical workload.

It is not yet a general autonomous experiment planner.

## 8. Next edge

After B467, compare the 32-side and 128-side specimens.

If both tile-size perturbations have negligible peak effect relative to the much
larger residency strategy effect from B463, then tile granularity should be
deprioritized and the active experiment surface should move to a stronger axis,
such as:

- lane concurrency;
- materialization policy;
- rematerialization cadence;
- workload size / pressure frontier.

That is exactly the kind of axis-selection decision the future governor should
learn from dogfood evidence.
