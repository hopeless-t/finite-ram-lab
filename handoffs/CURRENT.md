# CURRENT

> **Latest bounce:** B253
> **Stage:** STRATA-008 PASS / BOUNDED-WORKING-SET CAPACITY DECOUPLING
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## STRATA-008 PASS

Run:

`36437651740`

Launch SHA:

`1843e566c8cf6e18322861cd6c7ee51b28cccc30`

Aggregate:

- artifact id `10976142662`
- digest `sha256:8fbdf646686efe6923afd57e78c859b79ceeda9f2124b2c6fd6023de88909186`
- 24 / 24 trials
- PASS

## Capacity result

Cold capacity:

- 96 MiB anchor -> `80 < K <= 88`
- 192 MiB -> `80 < K <= 88`

Both:

`144 < K+hot <= 152 MiB`

Total work/advice activity increased, but the onset and retained DONTNEED floor stayed bounded.

Empirical bootstrap of DONTNEED non-hot floor:

- 96 MiB median: 12.8125 MiB
- 192 MiB median: 13.0546875 MiB
- observed shift: +0.2421875 MiB
- 95% bootstrap interval: approximately [-0.001953, +0.250000] MiB

Interpretation: bounded sub-MiB floor movement, not exact equality.

Full result:

`docs/STRATA-008-RESULT.md`

Bootstrap receipt:

`evidence/STRATA-008/empirical-bootstrap-v1.json`

## Leading mechanism

Current hosted evidence supports:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval`

rather than total one-shot dataset capacity.

## Next fresh-bounce action

Freeze STRATA-009 as a cold-capacity boundary test:

- cold file 384 MiB;
- MemoryMax remains 320 MiB;
- MemoryHigh remains 160 MiB;
- hot anon remains 64 MiB;
- same Ubuntu 26.04 runner, Python 3.12, read chunk, DONTNEED cadence panel, Recorder semantics;
- reuse 192 MiB as anchor.

Question: can total one-shot dataset capacity exceed the cgroup MemoryMax while instantaneous demand remains bounded?

Do not launch in the design bounce.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
