# finite-ram-research-loop

Repository-local compiled decision skill for Finite RAM Lab.

## Use

Before re-reading the full meta-research history, provide explicit facts to:

    python -m finite_ram_lab.fr_decision_skills --facts '{"key": true}'

Use only the returned matching skill capsules.

If the result is NO_COMPILED_DECISION, or the needed decision remains
unresolved, fall back to the full L0/L1/L2 research loop.

## Always-resident invariants

- UNKNOWN is not success.
- Missing evidence is not zero.
- Evidence and decision remain separate.
- Method improvement never expands execution authority.

## Boundaries

Compiled skills are cached research decisions, not authority.

A skill stops applying when one of its invalidation conditions becomes true.

Runtime benchmarks whose runtime is itself evidence must not be memoized away.

Cache optimizations require proven producer-to-consumer reuse before promotion.

Pre-receipt build-ahead is ephemeral; durable Git materialization begins only
after the parent receipt is frozen.
