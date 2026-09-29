# Bounce Handoff

> **Bounce ID:** B320
> **Status:** COMPLETE / MEMCG-005 IMPLEMENTED / NOT LAUNCHED

Implemented:
- dedicated zero-touch worker with TOUCH_ONE and bounded TOUCH_N
- 16-worker prestart per replica
- calibration-to-Q64 + 63-touch EMPTY normalization
- measured +64 verification for every wash/target/challenger insertion
- independent one-shot target probes for m={0,5,6,7,8}
- sparse boundary model competition K=1..9
- explicit observational equivalence classes
- leave-one-block-out analysis
- INVALID_STATE preservation
- synthetic tests and hosted workflow

Operational clarification:
PRESENT is implemented as abs(target_probe_delta) < 16 pages.
Large negative deltas are therefore AMBIGUOUS, not falsely classified as PRESENT.

No launch marker exists.

Next:
read ordinary CI for B320 exactly once.

Hosted research only.
