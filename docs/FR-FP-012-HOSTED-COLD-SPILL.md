# FR-FP-012 — Hosted calibrated RSS budget with file cold spill

Status: **HOSTED PHYSICAL COLD-SPILL CANDIDATE**

Parent: **FR-FP-011**

## Question

FR-FP-011 calibrated the frozen hosted fixture exactly:

    one live trajectory state = 8 MiB VmRSS / RssAnon

FR-FP-012 asks whether that calibration can drive a real physical hot-memory
budget while preserving live-but-not-yet-semantically-reclaimable state in a
cold file tier.

## Frozen budget

Process trajectory RSS budget:

    32 MiB

Calibrated hot-state budget:

    32 / 8 = 4 live states

Trajectory length:

    12 states

Synthetic safe endpoint:

    step 9

The safe step is deliberately later than the four-state hot budget.

Discarding old state before step 9 would violate the synthetic semantic
contract.

## Physical cold tier

Before allocating the next state, if four hot states already exist:

1. choose the oldest hot state;
2. write all 8 MiB to a regular file;
3. fsync the file;
4. verify sentinel bytes from the durable file;
5. close/unmap the anonymous hot state;
6. allocate/fault the next state.

This is proactive movement before the next allocation, not a reaction after the
RSS budget is exceeded.

At safe step 9:

- old hot mappings are closed;
- cold files are deleted;
- the current endpoint remains hot.

## Two memory accounting planes

Process RSS and cgroup memory are not treated as identical.

### Process plane

VmRSS / RssAnon answer:

> how much trajectory data is resident in this process?

The 32 MiB budget applies here.

### cgroup plane

memory.current, when available, can include charges that process RSS does not,
including file-backed page cache.

A file spill can therefore satisfy the process RSS budget while leaving part of
the data charged to the same cgroup.

FR-FP-012 records this instead of assuming that file-backed cold state is
physically free.

## Qualification

The mandatory gate requires:

- calibration maps 32 MiB to four hot states;
- hot live-state count never exceeds four;
- process RSS peak stays within budget plus 4 MiB measurement margin;
- five 8 MiB states are physically written before safe collapse;
- all spill sentinels verify before hot unmap;
- peak cold bytes are exactly 40 MiB;
- safe collapse leaves one hot state and zero cold files;
- final process RSS is one-state scale.

cgroup memory.current is observational in v0.1.

It is not made a PASS condition because the purpose is to discover the actual
page-cache accounting behavior first.

## Why this matters

The research chain is now:

    semantic deadline theory
      -> survival law
      -> physical bytes/state calibration
      -> physical RSS budget
      -> proactive hot-to-cold movement

This is the first hosted physical test where a semantic budget is translated
into a byte budget and used to control real state placement.

## Claim ceiling

**HOSTED_LINUX_PROCESS_RSS_BUDGET_AND_FILE_COLD_SPILL_ONLY**
