# FR-SOOM-002E — Latent Shared-Pressure Detector Qualification Receipt

Status: **PASS / SYNTHETIC HELD-OUT LATENT DETECTOR VALIDATED**

## Frozen qualification

- workflow run: 37015125446
- job: 110863993808
- execution head: c29e8945429974cbbfb5612ff4bffc291c9d0c1c
- targeted tests: 7/7 PASS
- artifact ID: 11230110487
- artifact ZIP SHA256: 6e7b9b44458aff4f18b8763844740c1f1ae70030e82e15c19cb3c3dd653cda25
- spec SHA256: 3d37938304f7aa0bf47efdceb5eef170afebec46b4ca7f8f5a4fedc0e015d35c
- result SHA256: dc9b96e28296580b5e02939dbdf868164bfddd3dd12f1479458849f53fbd5c34

## Frozen dataset

- total episodes: 8192
- train episodes: 4096
- held-out test episodes: 4096
- latent BAD prior: 8%
- training BAD episodes: 308
- held-out BAD episodes: 305
- early observation horizon: 50 ms

## Detector setup

Both detectors fit their threshold on the training set to achieve at least 95%
BAD-state recall.

### PSI_ONLY

Input:

- PSI full avg10 only.

### MULTI_SIGNAL

Inputs:

- PSI level;
- PSI slope;
- reclaim progress by 50 ms;
- refault ratio;
- cooperative progress by 50 ms;
- swap velocity.

The latent BAD label is never an inference input.

## Held-out result

Both detectors find exactly the same number of BAD episodes:

- true positive: 287
- false negative: 18
- recall: 0.9409836066

The difference is false escalation.

| detector | TP | FN | FP | TN | recall | false-positive rate | precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| PSI_ONLY | 287 | 18 | 2447 | 1344 | 0.940984 | 0.645476 | 0.104974 |
| MULTI_SIGNAL | 287 | 18 | 152 | 3639 | 0.940984 | 0.040095 | 0.653759 |

At matched held-out detection count, MULTI_SIGNAL removes:

`2295`

false escalations.

## Synthetic downstream cost projection

The harness assigns an artificial +5 semantic-loss delta to each unnecessary
escalation.

That produces:

- PSI_ONLY false-escalation delta: 12,235 points;
- MULTI_SIGNAL false-escalation delta: 760 points.

This cost exists only to make false-positive consequences visible.

It is not a measured user utility.

## Primary finding

In this fixture:

`pressure severity signal != shared failure-domain signal`.

PSI remains useful pressure telemetry, but a one-dimensional PSI threshold
cannot preserve the same BAD-state detection count without classifying a large
fraction of GOOD episodes as BAD.

Adding orthogonal early observables preserves the matched held-out detection
count while sharply reducing unnecessary escalation.

Therefore:

`multi-signal state quality can matter as much as action policy`.

## Architecture implication

The Semantic OOM stack now has a distinct inference plane:

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

The estimator should be calibrated separately from the intervention policy.

That prevents pressure sensing, latent-state inference, and destructive action
selection from collapsing into one opaque score.

## Limitation

FR-SOOM-002E still uses latent BAD labels to train the synthetic classifier.

A real host does not expose such labels.

Therefore this is detector-harness qualification, not the final inference
method.

## Claim ceiling

**SYNTHETIC_LATENT_PRESSURE_DETECTOR_ONLY**

No live process was controlled.

No threshold is proposed for a real machine.

## Next

FR-SOOM-002F should remove direct BAD labels from training.

A stronger observable-only route is to infer shared-domain evidence from outcome
traces:

- whether relief arrived before deadline;
- achieved relief;
- simultaneous late-action count;
- observed pressure trajectory.

Candidate methods:

- transition diagnostics;
- likelihood comparison;
- permutation-calibrated dependence statistics;
- run / co-failure tails.

This connects directly to the existing FR-CLM-001F direction: hidden dependence
should be inferred from traces rather than supplied by the generator.
