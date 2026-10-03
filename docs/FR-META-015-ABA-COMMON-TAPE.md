# FR-META-015 — Skill-routed ABA common stochastic tape

Status: **DOGFOOD PERFORMANCE CANDIDATE**

Parent: **FR-META-014**

## First prospective skill dogfood

This lane deliberately does not re-derive the full optimization protocol from
the FR-META history.

It asks the compiled decision router only:

- deterministic duplicate work = true;
- scientific contract unchanged = true;
- runtime is the measurement = false.

The expected compiled primary action is:

    REUSE_EXACT_COMPUTATION

and its Monte Carlo policy is:

    SKIP

If that skill does not match, this experiment fails closed.

## Duplicate work

After FR-META-006, A1 and A2 means are reused, but each observer arm still
regenerates the identical B-segment stochastic tape:

- noise;
- baseline tail event;
- baseline tail amplitude;
- observer-tail event.

NULL, LIGHT, and HEAVY therefore perform three stochastic B tape passes per
episode even though only the observer overhead values differ.

## Exact reuse

Generate the common B tape once per episode.

For each frame:

1. compute the common B value exactly as before;
2. compute the observer-tail boolean once;
3. copy that common float into each arm;
4. add that arm's constant overhead;
5. conditionally add that arm's tail overhead.

The arithmetic order inside each arm is preserved.

A direct reference test compares combined means against the original
_segment implementation for multiple frozen episodes and requires exact float
equality.

The full pre-existing ABA frozen result remains the final semantic guard.

## Structural effect

At 8,192 episodes and three arms:

- B stochastic tape passes: 24,576 -> 8,192;
- B tape generation reduction: 66.67%;
- segment loops per episode: 5 -> 3;
- overall segment-loop reduction: 40%.

No episode, frame, observer arm, threshold, or equivalence margin is changed.

## Why this matters

This is the first performance transition whose research-routing decision is
made by FR-META-014 rather than by rereading the full method history.

The skill capsule is therefore part of the experimental path, not merely
documentation.

## Claim ceiling

**SKILL_ROUTED_EXACT_TEST_HARNESS_OPTIMIZATION_ONLY**
