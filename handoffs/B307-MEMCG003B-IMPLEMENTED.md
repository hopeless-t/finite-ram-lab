# Bounce Handoff

> **Bounce ID:** B307
> **Status:** COMPLETE / MEMCG-003B IMPLEMENTED / NOT LAUNCHED

Implemented repaired seven-slot experiment.

Key changes:
- target is never touched during threshold observation;
- passive target memory.current only;
- one final target touch for recharge confirmation;
- Python orchestrator pinned to control CPU C;
- all wash/target/challenger workers pinned to separate stock CPU S.

Analysis:
- passive-drop threshold E
- candidate K=1..10
- absolute-error selection
- MDL/NLL selection
- Bayesian posterior
- leave-one-block-out prediction
- control-drop preservation

Reuses the already-tested C holder worker.

No launch marker exists.

Next: read B307 ordinary CI exactly once.

Hosted research only.
No local-PC execution.
