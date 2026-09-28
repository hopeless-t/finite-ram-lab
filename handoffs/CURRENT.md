# CURRENT

> **Latest bounce:** B283
> **Stage:** MEMCG-001 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## EVIDENCE-001

SQL corpus PASS and operational.

Canonicalized at:

`f3f4a89da97fc6f7bf344d4b9684a291502a8f41`

## MEMCG-001 implementation

Exact commit:

`ed930823ca0d02b1aa080f1b072fe26452bc28a0`

Purpose:
directly test whether memcg accounting exposes a reproducible 64-page / 256-KiB charge-batch structure.

Frozen implementation:
- Ubuntu 26.04
- low-noise C worker
- self-pinned CPU
- fresh transient cgroup
- page size must be 4096
- 256 one-page samples
- touch and no-touch control
- 4 blocks / 8 trials

Mathematics:
- baseline-corrected memory.current
- first differences
- significant-jump extraction
- Q={1,2,4,8,16,32,64,128} lattice search
- modulo-phase concentration
- jump spacing/change points
- autocorrelation
- control comparison
- preregistered SUPPORT_H64 / REJECT_H64 / INCONCLUSIVE

Ordinary CI:

`36448740557`

Single B283 read:

`queued`

Do not poll again in this bounce.

## Next fresh-bounce action

Read CI `36448740557` exactly once.

- success -> explicit MEMCG-001 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## LDC role

LDC is now useful for the next substrate-replication phase:
- checkout exact hosted candidate;
- compile the same C worker;
- execute under MVCA/LDC on Lubuntu;
- capture kernel/page-size/cgroup receipts;
- publish local evidence back to GitHub.

That local execution must use a separately fixed MVCA scope and approval.

## Authority boundary

Hosted repository/research only in current bounce.
No local-PC execution.
No memory-control policy.
