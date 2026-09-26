# EXP-001 Design Council — Residency Identity Swap

> **Status:** DESIGN STUDY

## Question

If the same amount of anonymous memory is removed from RAM, does performance depend on **which semantic region** loses residency?

## Pseudo-Council

### Causal-inference reviewer

Use the ENV-004 instrument under low pressure so broad `memory.high` throttling is absent.

Both arms must reclaim the same amount of memory.

Only the identity of the reclaimed semantic region changes.

### Application/runtime reviewer

Create two equal 16 MiB semantic regions:

- HOT — always reused immediately after the intervention;
- COLD — not reused during the primary outcome window.

Primary arms:

    HOT_EVICT:
      HOT gets MADV_PAGEOUT + proactive reclaim
      COLD stays resident
      then retouch HOT

    COLD_EVICT:
      COLD gets MADV_PAGEOUT + proactive reclaim
      HOT stays resident
      then retouch HOT

Total mapped bytes, swap preparation, reclaim request, and later HOT workload remain matched.

### Kernel / VM reviewer

This does not test whether the kernel naturally chooses the wrong page.

It tests whether residency identity is sufficient to alter next-use cost at matched capacity.

### Measurement reviewer

Verify intervention fidelity with `mincore(2)` before the primary retouch:

- selected target largely nonresident;
- non-target largely resident;
- content integrity preserved.

Trials failing instrument fidelity are INVALID, not negative scientific results.

### Statistics reviewer

Runner identity is the replication block.

Use mean log latency contrast per runner and exact block sign-flip inference.

### Monte Carlo reviewer

Choose runner/repeat allocation under moderate, heavy, and branchy log-latency noise.

Candidate designs:

    D1  6 blocks x 2 repeats/arm  = 24 trials
    D2  8 blocks x 2 repeats/arm  = 32 trials
    D3  8 blocks x 3 repeats/arm  = 48 trials
    D4 12 blocks x 2 repeats/arm  = 48 trials

Because independent runners are the top-level replication unit, prefer more blocks over extra within-runner repeats when trial cost is equal and detection is similar.

## Authority boundary

A positive result would establish causal importance of **residency identity** under the bounded experiment.

It would not establish that natural Linux reclaim is suboptimal or that an application/OS coordinator is beneficial.
