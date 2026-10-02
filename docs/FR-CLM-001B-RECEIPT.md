# FR-CLM-001B — Stochastic Rare-Event Qualification Receipt

Status: **PASS / SYNTHETIC STOCHASTIC HARNESS VALIDATED**

## Frozen qualification

- workflow run: 37001867894
- job: 110821161359
- execution head: 36109a48c30ae9ec463c8face678f53f1fbf3b4f
- targeted tests: 6/6 PASS
- artifact ID: 11223634679
- artifact ZIP SHA256: 8550f520138937096cf9e3cd945fe1df8237e766c5ee3bf80bf768e9581c14f0
- spec SHA256: 28c80c723e9e92dec87e9373540297f39be0691721d57b61b0ae8151c16c3ea1
- result SHA256: 4ccec4fa979dc605e57ef9463e233b75b47e7f715ed63a1e105045d5b9aeec35

## Primary result

Qualified pressure knee under the frozen rule:

- APPEND_TRUNCATE: **budget 8**
- NOISY_KEY_AWARE: **budget 2**

The qualification rule required both:

- exact rate >= 0.95;
- Wilson 95% lower bound >= 0.95.

## Rare-event result at budget 2

NOISY_KEY_AWARE:

- observations: **2,048**
- failures: **17**
- successes: **2,031**
- exact rate: **0.99169921875**
- failure rate: **0.00830078125**
- Wilson 95% interval: **[0.9867463946, 0.9948109237]**

The harness therefore preserved a qualified low-budget operating point while
still capturing non-zero rare semantic failures.

## Why this matters

A high average success rate is not enough evidence for a finite semantic
working-set policy.

FR-CLM-001B demonstrates that the experiment can simultaneously report:

1. resident-budget pressure;
2. uncertainty around the aggregate success rate;
3. low-frequency semantic omissions;
4. replayable failure-state biopsies.

This is the semantic analogue of the physical Finite RAM rule that tail events
must not be averaged away.

## Important non-claim

The 0.5% omission probability is injected synthetic test data.

It is not an empirical failure rate for CLM, Pi, KITten, any provider, or any
language model.

The budget-2 qualified knee is a property of this frozen synthetic corpus and
fixture only.

## Claim ceiling

**SYNTHETIC_STOCHASTIC_SEMANTIC_WORKING_SET_ONLY**

## Next

FR-CLM-001C should sweep selector reliability rather than fixing it at 0.5%.

The next surface is:

`resident budget x selector reliability -> semantic survival`

That surface should preserve rare-event biopsy and uncertainty reporting before
the lab moves to real model-managed context.
