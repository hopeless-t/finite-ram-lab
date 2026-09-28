# Bounce Handoff

> **Bounce ID:** B293
> **Status:** COMPLETE / MEMCG-002 CAUSAL DESIGN FROZEN

MATH-001 established MODEL64_WINS.

MEMCG-002 intervenes on CPU identity because upstream memcg stock is per-CPU.

Frozen arms per block:
- FIXED_TOUCH
- MIGRATE_TOUCH A->B at step128
- ROUNDTRIP_TOUCH A->B at128, B->A at192
- ROUNDTRIP_CONTROL with the same migrations and no page touches

4 blocks = 16 trials.

Key predictions:
- migration to fresh CPU B triggers +64 within 1-2 touches;
- B then retains Q64 spacing;
- returning to A restores old A modulo64 phase;
- migration control produces no staircase.

Next: implement only. Do not launch in implementation bounce.

Hosted research only.
