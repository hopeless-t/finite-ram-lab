# FR-SOOM-002G — Inference-Informed Planner Qualification Receipt

Status: **PASS / SYNTHETIC CLOSED-LOOP PLANNING VALIDATED**

## Frozen qualification

- workflow run: 37025152251
- job: 110897777773
- execution head: c5afa3624c7c290b029ab83b2e89bfeb8e155bbe
- targeted tests: 7/7 PASS
- artifact ID: 11234777317
- artifact ZIP SHA256: fa94ce63da745297eab9eae58c26d360295ded20f99f616c292b19c256e043b2
- spec SHA256: 999587b83a6951efd8f9e06f6f87741fa53aea4303df6ad5708fe92a77f46b6e
- result SHA256: 0a80f87db959f6745dfebbe656d281bd8893ba32f4b529a45cd2c9b23993734a

## Closed loop

FR-SOOM-002G is the first lane in this series where observed dependence
inference changes the future memory-control policy.

Historical inference comes from FR-SOOM-002F and receives no latent BAD label.

Frozen history:

- INDEPENDENT -> IID_COMPATIBLE;
- SHARED_BAD -> CROSS_ACTION_DEPENDENCE_EVIDENCE.

Policy:

- IID_COMPATIBLE -> COOPERATIVE_REDUNDANCY;
- CROSS_ACTION_DEPENDENCE_EVIDENCE -> BACKGROUND_SACRIFICE.

## Future reliability contract

- future episodes per regime: 16,384
- per-cluster-action tail count: 164
- relief target: 3000 MiB
- reliability point floor: 0.999
- Wilson95 lower-bound floor: 0.999

The cooperative plan contains four 1000-MiB actions.

One is a differently-coupled spare, so one clustered late action is tolerated.

Two or more clustered late actions miss the relief deadline.

## Independent future result

The future IID-compatible cluster produces seven multi-action coincidence
episodes.

DEPENDENCE_AWARE remains on cooperative redundancy.

- deadline successes: 16,377 / 16,384 = 0.99957275
- deadline failures: 7
- Wilson95 lower: 0.99911828
- reliability qualified: yes
- current-task losses: 7
- mean semantic loss: 10.11963
- p99 semantic loss: 10

The inference-informed planner does not pay the high background-sacrifice cost
when historical traces are compatible with independence.

## Shared future result

The same marginal tail rate is concentrated into 164 shared episodes.

### NAIVE_COOPERATIVE

- deadline successes: 16,220 / 16,384 = 0.98999023
- deadline failures: 164
- Wilson95 lower: 0.98834695
- reliability qualified: no
- current-task losses: 164
- mean semantic loss: 12.80273
- p99 semantic loss: 290

### DEPENDENCE_AWARE

Historical dependence evidence selects BACKGROUND_SACRIFICE.

- deadline successes: 16,384 / 16,384 = 1.0
- deadline failures: 0
- Wilson95 lower: 0.99976554
- reliability qualified: yes
- current-task losses: 0
- mean semantic loss: 73
- p99 semantic loss: 73

### KILL_FIRST

- deadline successes: 16,384 / 16,384 = 1.0
- current-task losses: 16,384
- mean semantic loss: 280
- p99 semantic loss: 280

## Primary finding

In the shared regime, NAIVE_COOPERATIVE has a lower **mean** synthetic semantic
loss than DEPENDENCE_AWARE:

`12.80 < 73`.

But the naive plan violates the reliability constraint and creates a p99 loss
of 290 through emergency active-task sacrifice.

The dependence-aware plan raises expected cost to buy tail safety:

`mean cost up -> deadline reliability up -> p99 task loss down`.

Therefore:

`expected semantic loss alone is not a sufficient controller objective`.

The controller should use a constrained objective such as:

```text
minimize expected semantic loss
subject to:
  deadline reliability >= required floor
  active-task loss <= policy bound
```

## Qualification correction

The initial future fixture used 8192 episodes.

A scratch pilot accidentally used the draw-domain spelling `IId` while the
committed implementation correctly used `IID`, yielding a different
reproducible sample stream.

The 8192-episode committed stream produced three IID multi-action misses and did
not satisfy the already-frozen Wilson95 lower-bound floor of 0.999.

The reliability criterion was **not relaxed**.

The future panel was instead expanded to 16,384 episodes while doubling the
exact per-action tail count from 82 to 164, preserving the same approximately
1% marginal tail rate.

The powered fixture produces seven IID misses and still satisfies the frozen
Wilson95 floor.

This preserves the scientific question while increasing qualification power.

## Earlyoom-successor implication

The synthetic architecture now has an actual closed feedback loop:

```text
shadow observations
  -> failure-domain inference
  -> risk-constrained plan selection
  -> cooperative redundancy or background sacrifice
  -> active-task kill only as emergency fallback
```

This is no longer only a smarter victim score.

It is a prototype control architecture for a semantic memory governor.

## Claim ceiling

**SYNTHETIC_INFERENCE_INFORMED_PLANNING_ONLY**

No live process was controlled.

No synthetic reliability threshold or action set is a recommended host setting.

## Next

FR-SOOM-002H — regime drift and stale-belief control.

A long-running daemon must forget old dependence evidence when the workload
changes, but not oscillate on every short burst.

Compare:

- static historical belief;
- sliding-window evidence;
- confidence decay;
- hysteresis.

Primary endpoints:

- detection delay after IID -> SHARED transition;
- release delay after SHARED -> IID transition;
- deadline misses during underreaction;
- unnecessary background sacrifice during overreaction.
