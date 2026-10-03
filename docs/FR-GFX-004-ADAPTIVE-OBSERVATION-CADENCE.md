# FR-GFX-004 — Adaptive Observation Cadence

Status: **SYNTHETIC OBSERVATION-CADENCE MODEL**

Parent: **FR-GFX-003**

## Question

Once we know which signals matter, how often should expensive signals be
sampled?

On a low-end machine, an observer can become part of the workload it is trying
to measure.

Sampling cadence therefore belongs in the resource-control model.

## Periodic detection model

Assume an event of duration d starts at a uniformly random phase relative to a
periodic sampler with interval Delta.

The probability that at least one sample lands inside the event is:

[
P_{detect}(d,\Delta)=\min(1,d/\Delta).
]

For a duration distribution:

[
P_{detect}(\Delta)=
\sum_i p_i\min(1,d_i/\Delta).
]

The frozen synthetic event-duration distribution is:

| duration | probability |
|---:|---:|
| 50 ms | 25% |
| 100 ms | 35% |
| 250 ms | 25% |
| 1000 ms | 15% |

This is not a measured game trace.

## Fixed-cadence result

| interval | detection | samples/s |
|---:|---:|---:|
| 50 ms | 100% | 20 |
| 100 ms | 87.5% | 10 |
| 250 ms | 59% | 4 |
| 500 ms | 37% | 2 |
| 1000 ms | 26% | 1 |

The tradeoff is direct: more telemetry buys more transient capture.

## Adaptive observation

Now keep an expensive source at 500 ms normally.

A cheap frame anomaly trigger has 90% recall.

When it fires, expensive telemetry is sampled every 50 ms for 500 ms.

At a frozen harmful-event rate of 0.2/s:

- expected expensive sampling rate: **3.8 samples/s**;
- expected detection probability: **93.7%**.

Compared with always sampling at 50 ms:

- detection falls from 100% to 93.7%;
- sample volume falls by **81%**.

The adaptive policy also dominates the frozen 100 ms and 250 ms fixed policies:

- higher detection probability;
- lower sample rate.

## Detection SLO math

Let slow-sampler detection be P_s and cheap-trigger recall be q.

With immediate burst sampling after a trigger:

[
P_{adaptive}=P_s+q(1-P_s).
]

For the frozen 500 ms base sampler, P_s=0.37.

To guarantee a 90% synthetic detection target:

[
q \ge
\frac{0.90-0.37}{1-0.37}
=
0.8412698.
]

So the cheap trigger must have at least about **84.13% recall** for that SLO.

## When does adaptive stop being cheaper?

The frozen 50 ms sampler costs 20 samples/s.

The 500 ms base costs 2 samples/s.

With a 500 ms burst window, adaptive sampling reaches the same sample rate as
always-fast monitoring only when harmful anomalies occur at:

[
2.0 events/s.
]

Below that synthetic rate, escalation remains cheaper.

## Finite RAM interpretation

Observation now has the same architecture as the rest of the lab:

```text
cheap state
   ↓
weak evidence
   ↓
cheap continuous observer
   ↓ ambiguity / anomaly
expensive observation burst
   ↓
diagnosis
```

This is **representation / residency escalation for evidence itself**.

## Low-FPS relevance

For a game already near 10 FPS, a 100 ms frame is ordinary.

Sampling every 50 ms with multiple heavy collectors may therefore be a
meaningful perturbation.

The live experiment must measure observer overhead instead of assuming the
sample-count model is sufficient.

## Next

### FR-GFX-005 — Observer perturbation protocol

A-B-A read-only runs:

1. game only;
2. cheap observation plane;
3. full observation plane;
4. cheap + adaptive burst plane;
5. game only again.

Endpoints:

- median/p95/p99 frametime;
- game RSS/PSS;
- MemAvailable;
- memory PSI;
- observer CPU/RSS;
- log bytes/s;
- GPU telemetry availability;
- backend identity.

The observer is qualified only if its perturbation is below a frozen budget.

## Claim ceiling

**SYNTHETIC_OBSERVATION_CADENCE_MODEL_ONLY**
