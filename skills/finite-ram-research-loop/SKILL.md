# finite-ram-research-loop

Repository-local compiled decision skill for Finite RAM Lab.

## Use

Before re-reading the full meta-research history, provide explicit facts to:

    python -m finite_ram_lab.fr_decision_skills --facts '{"key": true}'

Use only matching capsules whose lifecycle state remains resident-eligible.

If no compiled decision matches, evidence is unresolved, or the matching skill
is retired/blocked, fall back to the full L0/L1/L2 research loop.

## Always-resident invariants

- UNKNOWN is not success.
- Missing evidence is not zero.
- Evidence and decision remain separate.
- Method improvement never expands execution authority.

## Lifecycle

- CANDIDATE: not resident by default.
- QUALIFIED: resident.
- STABLE: resident.
- QUALIFIED_NEGATIVE: resident scoped guard.
- RETIRED: cold history only.
- BLOCKED / INSUFFICIENT_EVIDENCE: not resident.

The lifecycle governor may update maturity only. It cannot silently rewrite a
skill's trigger or action.

## Boundaries

Runtime benchmarks whose runtime is evidence must not be memoized away.

Cache optimizations require proven producer-to-consumer reuse before promotion.

Pre-receipt build-ahead is ephemeral; durable Git materialization begins only
after the parent receipt is frozen.

Retiring a skill evicts it from resident context but never deletes its evidence.
