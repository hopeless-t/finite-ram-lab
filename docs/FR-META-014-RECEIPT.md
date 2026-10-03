# FR-META-014 Receipt

Status: **PASS / DECISION SKILL COMPILER QUALIFIED**

- workflow run: 37139721850
- job: 111251459625
- execution head: db68cc1ea77028705901919dc6acc644717408db
- qualification artifact ID: 11279497784
- artifact ZIP SHA256: 0ac2e3e8f344b0393738471cb5d82a856b4d0f00f1e5bedcb3e6321c8b46cb97

Compiled source surface:

- FR-META-004 through FR-META-013 docs: 10 files / 17,417 characters
- compiled decision skills: 13
- serialized full catalog: about 3,778 characters
- catalog reduction versus frozen source surface: about 78.3%
- typical selected exact-reuse capsule with invariants: about 409 characters
- selected-context reduction versus frozen source surface: about 97.6%

Qualified behavior:

- explicit fact predicates select compact decision capsules;
- UNKNOWN / missing trigger facts do not guess;
- runtime benchmarks are protected from memoization when runtime is evidence;
- exact deterministic duplicate work routes to exact reuse before sample reduction;
- exact topology may skip Monte Carlo;
- uncertain loss-sensitive decisions route to Monte Carlo;
- main CI remains non-cancelable;
- non-main same-head duplicate CI may be cancelled;
- pre-receipt build-ahead remains ephemeral;
- cache promotion is rejected when producer -> consumer restore is unproven;
- failure biopsy remains a compiled guard.

Authority:

Decision skills reduce context and re-reasoning only.
They do not grant execution authority.

Decision:

**COMPILE_REPEATED_RESEARCH_DECISIONS_INTO_SMALL_SKILL_CAPSULES**

Next dogfood:

Use the compiled EXACT_REUSE skill to route the next ABA duplicate stochastic
tape optimization without re-reading the full meta-history.

Claim ceiling:

**COMPILED_DECISION_ROUTING_AND_CONTEXT_SURFACE_ONLY**
