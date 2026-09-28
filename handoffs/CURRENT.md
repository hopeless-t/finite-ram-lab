# CURRENT

> **Latest bounce:** B301
> **Stage:** MEMCG-003 DESIGN FROZEN / IMPLEMENTATION NEXT
> **Turn stop reason:** SHORT_BOUNCE_CHECKPOINT

## Accepted chain

MEMCG-001: `SUPPORT_H64`
MATH-001: `MODEL64_WINS`
MEMCG-002: naive durable per-CPU-stock model rejected; CPU-conditioned phase remains favored.

Canonical MEMCG-002 result:
`docs/MEMCG-002-RESULT.md`

## B301

MEMCG-003 design:
`docs/MEMCG-003-SEVEN-SLOT-OCCUPANCY-v1.md`

Design commit:
`a51ee50ff85af00190f5d602a1a9f1c29eaf736e`

Status:
`DESIGN FROZEN / NOT LAUNCHED`

Question:
Can controlled distinct-memcg occupancy expose the source-derived `NR_MEMCG_STOCK = 7` boundary?

Arms:
- helper count k=0..10 on target CPU;
- same-helper-memcg control;
- other-CPU locality control.

Measurements include:
- target/helper memory.current;
- memory.stat;
- memory.events;
- PSI memory where readable;
- insertion/re-touch latency;
- pages/sec and cgroup lifecycle cost;
- environment/affinity receipts.

Monte Carlo design diagnostic:
50,000 sweeps, 3% observation flips, 5% missing.
- true boundary 7 -> exact 7 selected 86.6%;
- no-boundary null -> spurious exact 7 about 0.29%.
These are design diagnostics, not p-values.

Pseudo-Council:
APPROVE design freeze.
Do not approve launch.

## Next short bounce

Implement hosted MEMCG-003 runner/analyzer/workflow and synthetic tests.
Ordinary implementation CI must pass before any explicit launch marker.
No experiment execution merely because workflow code exists.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No Remote Desktop Commander.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
