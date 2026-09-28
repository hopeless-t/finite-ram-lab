# Bounce Handoff

> **Bounce ID:** B303
> **Status:** EXTERNAL_WAIT / MEMCG-003 IMPLEMENTATION CI IN PROGRESS

Implementation commit:
`b64f32ad3b38d4a6ca8bdfda36e4c12fe62d5569`

Ordinary CI:
`36459629772`

Single B303 status read:
`in_progress`

No second read was performed.

MEMCG-003 is implemented but not launched.

Core experiment:
- seven persistent wash memcgs
- persistent target
- distinct challengers
- target stock-drop / fresh-recharge separation
- same-memcg / six-only / no-churn controls
- K=1..10 model competition

Source prediction:
`K = 7`

Next fresh bounce:
- read CI `36459629772` exactly once;
- success -> explicit MEMCG-003 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
