# Bounce Handoff

> **Bounce ID:** B296
> **Status:** MEMCG-002 ANALYZER REPAIRED / CI PENDING

Failed CI:
`36454940719`

Exposed invariant:
`MIGRATE_TOUCH` B-side spacing was computed only through step192, although CPU B remains active through step256.

Repair commit:
`3e563db223c80938a09a8a1567c8b9fe4e5836d4`

Repair:
- MIGRATE_TOUCH B-side = all positive events after step128;
- roundtrip arms retain B-side = steps129..192.

No scientific hypothesis, trial design, or preregistered causal criterion changed.
No launch was issued.

Next: read ordinary CI for repair commit exactly once.

Hosted research only.
