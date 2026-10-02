# FR-SOOM-002E — Latent Shared-Pressure Detector

Status: **SYNTHETIC HELD-OUT DETECTOR QUALIFICATION**

## Goal

FR-SOOM-002D introduced a shared BAD failure domain, but the controller had
generator-level knowledge of that state.

A real controller will not.

FR-SOOM-002E asks whether an early observation vector can detect a latent shared
pressure state before the 200-ms intervention deadline.

The detector is allowed to observe only information available by the first
50 ms of the synthetic episode.

## Frozen early-observable features

- memory PSI full avg10;
- PSI slope;
- reclaim progress by 50 ms;
- refault ratio;
- cooperative-action progress by 50 ms;
- swap velocity.

The latent BAD label is used only for synthetic training/evaluation.

It is not an inference input.

## Dataset

- 8192 deterministic synthetic episodes;
- first 4096 = training;
- second 4096 = held-out test;
- latent BAD prior = 8%.

Frozen counts:

- training BAD: 308;
- held-out BAD: 305.

## Detectors

### PSI_ONLY

One threshold on PSI full avg10.

The threshold is set on training data to achieve at least 95% BAD-state recall
while remaining as high as possible.

This is a deliberately simple pressure-only baseline.

### MULTI_SIGNAL

An equal-weight normalized risk score over:

- PSI level;
- PSI slope;
- low reclaim progress;
- refault;
- low cooperative progress;
- swap velocity.

Its threshold is fitted under the same training recall rule.

## Frozen held-out result

Both detectors catch exactly:

- 287 / 305 BAD episodes;
- 18 false negatives;
- recall = 0.940984.

The difference is false escalation.

| detector | held-out TP | FN | FP | TN | recall | false-positive rate | precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| PSI_ONLY | 287 | 18 | 2447 | 1344 | 0.940984 | 0.645476 | 0.104974 |
| MULTI_SIGNAL | 287 | 18 | 152 | 3639 | 0.940984 | 0.040095 | 0.653759 |

At matched held-out detection count, the multi-signal detector avoids:

`2447 - 152 = 2295`

false escalations.

## Synthetic policy-cost projection

For this harness only, one unnecessary escalation is assigned a +5 semantic-loss
delta relative to staying on the cooperative path.

That yields held-out false-escalation cost:

- PSI_ONLY: 12,235 synthetic points;
- MULTI_SIGNAL: 760 synthetic points.

This is not a user-utility estimate.

It exists to make the controller consequence of false positives explicit.

## Primary finding

`pressure severity signal != shared failure-domain signal`.

PSI is useful pressure telemetry, but in this fixture one scalar PSI threshold
cannot distinguish BAD from non-BAD episodes without a very large false-positive
surface.

Adding orthogonal early signals preserves the same held-out BAD detection count
while dramatically shrinking unnecessary escalation.

Therefore:

`multi-signal state quality can matter as much as action policy`.

## Controller implication

The Semantic OOM architecture now has another distinct plane:

```text
pressure observer
      |
      v
latent failure-domain estimator
      |
      v
deadline-aware action planner
      |
      v
cooperative action / escalation
```

The estimator should remain separate from the action policy so each can be
calibrated and falsified independently.

## Important non-claim

All feature distributions are synthetic.

The PSI threshold and multi-signal threshold are not host settings.

The held-out result does not establish real Linux predictive performance.

No live process is controlled.

## Claim ceiling

**SYNTHETIC_LATENT_PRESSURE_DETECTOR_ONLY**

## Next

FR-SOOM-002F should remove direct BAD-state labels from the training interface.

A stronger path is to learn from observable outcomes instead:

- did relief arrive before deadline?
- how much relief arrived?
- how many supposedly independent actions were late together?

Then infer shared-domain evidence from outcome traces using likelihood,
transition, or permutation-based diagnostics.

That would align with the earlier FR-CLM-001F direction: infer hidden
dependence from observed traces rather than generator labels.
