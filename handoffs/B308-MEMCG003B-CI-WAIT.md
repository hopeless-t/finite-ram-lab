# Bounce Handoff

> **Bounce ID:** B308
> **Status:** EXTERNAL_WAIT / MEMCG-003B IMPLEMENTATION CI IN PROGRESS

Implementation:
`985d4efe4ebaa2eb877d2ad307bac630279d14d6`

Ordinary CI:
`36469054700`

Single B308 status read:
`in_progress`

No second read was performed.

MEMCG-003B repairs:
- passive target observation during churn;
- no target touch during threshold inference;
- exactly one final target recharge-confirmation touch;
- orchestrator pinned to control CPU;
- all cache workers pinned to a separate stock CPU.

Primary passive threshold:
`E_drop = first target memory.current drop >=16 pages`

Candidate K:
`1..10`

MATH-002 pmndrs/math geometric lens remains frozen and will be applied only after clean canonical MEMCG-003B evidence exists.

Next fresh bounce:
- read CI `36469054700` exactly once;
- success -> explicit MEMCG-003B launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
