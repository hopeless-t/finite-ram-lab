# FR-SOOM-002D — Correlated Tail Risk-Shape Qualification Receipt

Status: **PASS / SYNTHETIC CORRELATED-TAIL RISK SHAPE VALIDATED**

## Frozen qualification

- workflow run: 37014550688
- job: 110862101354
- execution head: 0f369e5404ba14ac8ad40457edfe9af16a9efb7a
- targeted tests: 7/7 PASS
- artifact ID: 11229890612
- artifact ZIP SHA256: 2239eec88215a38740a15aa631b8f8227892128fb92b6b6bf35844e8f143e7b4
- spec SHA256: 32dc100201006a1eb4e40639699c70fdbe9d55512aa56e65ffa51d88bdfae159
- result SHA256: eaef0adc167ef26519a7c376c1ede482f7270d164af363cc7c62fe196051baa6

## Matched marginal contract

The panel contains 16,384 replicates.

Each of the three cooperative actions receives exactly 164 tail replicates in
both arms:

`164 / 16384 = 0.010009765625`.

Therefore the finite-sample per-action marginal tail rate is exactly matched.

Only the cross-action dependence structure changes.

## Result

| metric | INDEPENDENT | SHARED_BAD |
|---|---:|---:|
| per-action tail count | 164 each | 164 each |
| affected episodes | 484 | 164 |
| affected rate | 0.029541 | 0.010010 |
| deadline success rate | 0.970459 | 0.989990 |
| multi-action tail episodes | 8 | 164 |
| conditional mean tail-action count | 1.016529 | 3.000000 |
| conditional p95 tail-action count | 1 | 3 |
| conditional mean relief deficit | 1016.53 MiB | 3000 MiB |
| conditional p95 relief deficit | 1500 MiB | 3000 MiB |
| conditional max relief deficit | 2400 MiB | 3000 MiB |

## Primary finding

The shared-BAD arm affects fewer episodes because the same marginal action-tail
events overlap.

However, when the shared state hits, all three cooperative actions are late and
the full 3000-MiB relief target is absent at the deadline.

Therefore:

`matched marginal action tails != matched controller risk shape`.

And:

`lower affected prevalence != lower conditional severity`.

The shared arm must not be described as globally safer simply because its
deadline-success rate is higher in this fixture.

The risk has been concentrated:

`broad + shallow != narrow + deep`.

## Failure-domain implication

A future controller cannot assume that parallel cooperative actions provide
independent chances of relief.

Actions may share a constrained substrate such as:

- CPU scheduling;
- reclaim progress;
- swap/storage I/O;
- memory bandwidth;
- allocator or VM locks;
- pressure-notification delivery.

The policy surface therefore needs an explicit failure-domain or correlation
group in addition to latency, relief, and semantic cost.

A candidate action descriptor becomes:

```text
action
  relief distribution
  latency distribution
  semantic cost
  failure domain
  correlation group
```

## Methodological transfer

This result directly reuses an earlier Finite RAM principle:

`prevalence != severity != mechanism`.

A one-dimensional failure rate is not enough to characterize the controller.

## Claim ceiling

**SYNTHETIC_CORRELATED_TAIL_RISK_SHAPE_ONLY**

No live process was controlled.

The shared BAD state is a synthetic mechanism, not an observed Linux state.

## Next

FR-SOOM-002E should introduce an observable latent-pressure-state classifier.

The task is not to know the generating arm.

The classifier should receive only observable pressure/action-response features
and estimate whether the episode is compatible with a shared failure domain.

Candidate features:

- PSI level and slope;
- reclaim progress;
- swap velocity;
- refault rate;
- number of simultaneously delayed actions;
- achieved relief by deadline.

The next scientific question is:

> Can a controller detect shared-domain risk early enough to escalate before
> the cooperative action ladder loses its deadline?
