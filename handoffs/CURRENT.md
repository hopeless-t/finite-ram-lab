# CURRENT

> **Latest bounce:** B281
> **Stage:** MEMCG-001 PAGE-CHARGE QUANTIZATION DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## EVIDENCE-001

SQL corpus PASS.

It rediscovered:
- pressure fixed-knee contradiction;
- common live-set transform `144 < K+hot <= 152`;
- capacity-knee invariance across 96/192/384 MiB;
- clean-floor span 0.248046875 MiB.

## MEMCG-001

Direct falsification test for a candidate discrete accounting structure.

Upstream mechanism candidate:
- `MEMCG_CHARGE_BATCH = 64U`
- with 4 KiB base pages -> 256 KiB

Frozen hosted experiment:
- Ubuntu 26.04
- C worker
- page size must be 4096
- fresh transient cgroup per trial
- self-pin to one CPU
- 256 one-page samples
- touch and no-touch control
- 4 blocks
- 8 trials

Analysis:
- baseline-corrected `memory.current`
- first differences
- significant jump magnitudes
- Q lattice search
- modulo phase
- jump spacing
- autocorrelation
- control comparison

Decision:
- SUPPORT_H64 only with >=3/4 block replication under preregistered magnitude/spacing criteria;
- REJECT_H64 for stable contrary evidence;
- otherwise INCONCLUSIVE.

Design:
`docs/MEMCG-001-PAGE-CHARGE-QUANTIZATION-v1.md`

## Next fresh-bounce action

Implement:
- C worker
- Python schedule/aggregate/math analyzer
- spec
- Ubuntu 26.04 workflow
- tests

Do not launch during implementation.

## LDC

LDC makes later local replication practical:
- local checkout/test/build;
- actual Lubuntu kernel/cgroup receipt;
- exact same worker and analyzer;
- GitHub publication afterward.

But local execution requires its own MVCA scope/approval/binding.

## Authority boundary

Hosted repository/research work only in current bounce.
No local-PC execution.
No memory-control policy.
