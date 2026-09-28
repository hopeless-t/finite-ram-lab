# Bounce Handoff

> **Bounce ID:** B259
> **Status:** COMPLETE / STRATA-009 PASS / DATASET > MEMORYMAX SUCCEEDED

STRATA-009 run `36440093666`: PASS, 20/20.

384 MiB dataset > MemoryMax 320 MiB completed under all bounded-policy arms with no OOM/OOM-kill.

Onset remained:

`80 < K <= 88 MiB`

matching 96 and 192 MiB studies.

Empirical 192->384 bootstrap found a +0.2421875 MiB median non-hot-floor shift, but the residency observer maps the whole file before post-scan memory measurement.

Therefore:
- capacity-decoupled knee: accepted;
- fine floor-growth law: HOLD pending observer-only audit.

Next: freeze an observer-footprint study at 96 / 192 / 384 MiB.

Hosted research only. No local-PC execution or memory-control policy.
