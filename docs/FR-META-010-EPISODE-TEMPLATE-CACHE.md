# FR-META-010 — Real-State Episode Template Cache

Status: **DETACHED PROVISIONAL UNTIL FR-META-009 RECEIPT**

Parent: **FR-META-009**

## Hotspot

The KSLA real-state panel evaluates 512 deterministic episodes under six
policies.

Every policy currently rebuilds the same episode target and cache permutation,
including repeated SHA-256 keying and sorting.

Recent CI showed this test family at roughly 11 seconds.

## Optimization

Cache one immutable episode template per episode:

- target tuple;
- permutation tuple.

Each policy still receives fresh list copies before execution.

This preserves the original mutable-list and state-isolation semantics while
sharing only deterministic setup work.

Structural template builds:

- baseline: 512 x 6 = 3,072;
- candidate: 512;
- reduction: 83.33%.

## Scientific guard

The existing frozen per-policy results remain the authority.

If any success count, mean rounds, work cost, refresh cost, or resident-view
result changes, the pre-existing test must fail.

No episode count, policy, proposal rule, or random source changes.

## Why no Monte Carlo

The candidate removes exact repeated deterministic fixture construction. It
does not alter an uncertain scientific decision.

## Claim ceiling

**TEST_HARNESS_TEMPLATE_REUSE_ONLY**
