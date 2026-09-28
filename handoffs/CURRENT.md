# CURRENT

> **Latest bounce:** B280
> **Stage:** EVIDENCE-001 PASS / READY FOR MEMCG QUANTIZATION DESIGN
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## SQL corpus

Run `36447185071`: PASS.

Canonical artifact:
- `corpus.sqlite`
- `query-results.json`
- `query-results.md`
- artifact id `10981205287`

Rediscovered:
- pressure fixed raw-knee intersection empty;
- common live-set transform `144 < K+hot <= 152 MiB`;
- capacity knee invariant at `80 < K <= 88 MiB` across 96/192/384 MiB;
- clean floor span 0.248046875 MiB.

## New mechanism candidate

Current Linux source defines:

`MEMCG_CHARGE_BATCH = 64U`

With 4 KiB pages this corresponds to:

`256 KiB`

The ~256 KiB structure seen in REC-003/004 is therefore worth a direct falsification experiment.

This is not yet an accepted law.

## Next fresh-bounce action

Freeze MEMCG-001:

- anonymous allocation in one-page (4 KiB) steps;
- fresh cgroup per trial;
- measure memory.current and selected memory.stat;
- include a no-touch measurement control;
- sample at least through 128 pages, preferably 192 pages;
- analyze first differences, jump spacing, modulo residue, candidate lattice width, and change points at 32/64/128 pages;
- replicate across independent blocks;
- preserve exact kernel/page-size/environment receipt.

Hosted experiment first.
Local LDC replication is a later substrate-replication action requiring its own MVCA-bound execution scope.

## Authority boundary

Hosted repository/research work authorized.
No local-PC execution in this bounce.
No memory-control policy.
