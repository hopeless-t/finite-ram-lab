# CURRENT

> **Latest bounce:** B248
> **Stage:** STRATA-008 COLD-CAPACITY INVARIANCE DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Canonical mechanism evidence

Across STRATA-005/006/007, the leading tested mechanism is:

`K ~= MemoryHigh - effective_live_set`

It has survived:

- pressure variation
- hot/live-set variation
- Ubuntu hosted-image variation

STRATA-007 Ubuntu 26.04 anchor:

- cold file 96 MiB
- `80 < K <= 88 MiB`
- `144 < K+hot <= 152 MiB`
- DONTNEED non-hot floor median 12.8125 MiB

## STRATA-008 frozen design

Change only total one-shot cold capacity:

- cold file 192 MiB

Hold:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials
- REC-001 density unchanged

Question:

Does doubled total cold capacity preserve the same onset and retained-floor bounds while increasing only total work/advice activity?

Design:

`docs/STRATA-008-COLD-CAPACITY-v1.md`

## Recorder sidecar repair

STRATA-007 environment receipts had blank `systemd_version`.

STRATA-008 must use:

`systemd-run --version | head -n1`

for the version receipt.

## Monte Carlo

Deferred until doubled-capacity physical evidence exists.

## Next fresh-bounce action

Implement STRATA-008:

- spec
- deterministic scheduler/trial/aggregate
- Ubuntu 26.04 hosted workflow
- repaired environment receipt
- regression tests

Do not launch during implementation.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-008 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
