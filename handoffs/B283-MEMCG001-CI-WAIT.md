# Bounce Handoff

> **Bounce ID:** B283
> **Status:** EXTERNAL_WAIT / MEMCG-001 IMPLEMENTATION CI QUEUED

Exact implementation commit:

`ed930823ca0d02b1aa080f1b072fe26452bc28a0`

Ordinary CI:

`36448740557`

Single status read in B283:

`queued`

No second read was performed.

MEMCG-001 is implemented but not launched.

Frozen implementation:
- C worker
- fresh cgroup per trial
- CPU pinning
- 4096-byte page requirement
- 256 one-page steps
- touch/control modes
- 4 blocks / 8 trials
- first differences
- lattice search
- modulo phase
- jump spacing
- autocorrelation
- preregistered H64 decision

Next fresh bounce:
- read CI `36448740557` exactly once;
- success -> explicit MEMCG-001 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Local LDC replication remains future and requires a separate MVCA-bound execution scope after hosted evidence exists.

Hosted research only.
No local-PC execution.
No memory-control policy.
