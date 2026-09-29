# MEMCG-004 Calibrated Stock Result v1

> **Status:** PASS / SUPPORT_CALIBRATED_STOCK
> **Run:** `36541998246`
> **Launch commit:** `bb36429bfdbd172fede04b66dbabf633e9b1ab4a`
> **Aggregate artifact id:** `11020158779`
> **Aggregate digest:** `sha256:b88c2fadf222cb8e29802f1a8d42826d250b1196b7b3cef3bcf5dbdb89608470`

## Primary decision

`SUPPORT_CALIBRATED_STOCK`

Support blocks:

`4 / 4`

The preregistered calibrated residual-stock phase was reproduced exactly in every block.

## Calibration events

CALIBRATED first fresh Q64 charge:

| block | calibration touch | calibration delta |
| ---: | ---: | ---: |
| 0 | 2 | +64 pages |
| 1 | 5 | +64 pages |
| 2 | 5 | +64 pages |
| 3 | 4 | +64 pages |

Worker READY receipts all asserted:

- CPU = 1
- page size = 4096
- measured pages touched before READY = 0

Thus startup phase varied, but the experiment did not assume startup phase.

It conditioned on an observed fresh +64 event.

## Passive hold

After the calibration event, CALIBRATED arms performed the frozen passive hold.

Maximum observed passive target-current drop:

`[0,0,0,0] pages`

Therefore the calibrated state survived the hold in 4/4 blocks.

## Consumption validation

After the hold, each CALIBRATED arm resumed one-page touches.

Exact result in every block:

- validation touches 1..63: delta = 0 pages
- validation touch 64: delta = +64 pages

Thus:

`R = [64,64,64,64]`

No phase jitter was observed.

## NO_HOLD control

Calibration touches:

`[2,6,7,3]`

Every calibration event was exactly +64 pages.

Without the passive hold, validation again produced:

`R = [64,64,64,64]`

Therefore the hold procedure is not required to create the phase and did not manufacture it.

## CONTROL_NO_PRIME

Without conditioning on a fresh +64 event:

`R = [5,5,3,4]`

The arbitrary startup phase therefore does not reproduce the calibrated R=64 phase.

## Model competition

Candidate residual phase:

`R in 1..128`

Total absolute error is uniquely minimized at:

`R = 64`

with:

`absolute_error(R=64) = 0`

Description lengths reported by the frozen analyzer:

- arbitrary event locations: 28 bits
- fixed R64 model: 7 bits

Compression advantage:

`21 bits`

## Mechanism interpretation

For a one-page demand on a stock miss, the inspected Linux source:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

uses:

`MEMCG_CHARGE_BATCH = 64`

and refills the unused portion of the batch into the current CPU's memcg stock.

The observed sequence is exactly source-consistent with:

- +64 pages charged at calibration;
- 1 requested page consumed;
- 63 pages retained as cached stock;
- validation touches 1..63 consume that stock without another batch charge;
- validation touch 64 misses the exhausted stock and triggers the next +64 batch.

MEMCG-004 therefore establishes a reproducible way to create an **experimentally calibrated stock phase**.

This is stronger than inferring slot occupancy from worker existence.

## What this does not establish

MEMCG-004 does not yet establish:

- seven-slot cache capacity;
- eviction order;
- cross-memcg slot replacement behavior;
- a hardware-memory law.

It establishes a controlled initial condition for those experiments.

## Next experiment

MEMCG-005 should build the seven-slot experiment only from independently calibrated stock states:

1. calibrate seven persistent wash memcgs;
2. calibrate a persistent target memcg;
3. calibrate distinct persistent challengers one-by-one;
4. never consume the target during challenger insertion;
5. after each challenger, use a bounded target state test designed not to destroy subsequent capacity inference, or use separate one-shot target replicas per challenger count;
6. compare candidate eviction counts while preserving the calibrated-state guarantee.

A one-shot-replica design is preferred if sequential target probing would mutate the target stock state.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
