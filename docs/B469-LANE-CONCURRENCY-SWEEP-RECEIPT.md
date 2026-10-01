# B469 — Residue Lane Concurrency Sweep Receipt

Status: **PASS / FIRST PHYSICAL q FRONTIER**

## Frozen execution

- workflow run: 36929489065
- job: 110594945828
- execution head: 81e1c3951b097bddba991633383489389f85132c
- tests: 4/4 PASS
- artifact ID: 11195606726
- artifact ZIP SHA256: 81bc983bc90a7cc6e880c372ae6bfeb95845acf9ea28a55b75ae2a3ea0e37db4
- sweep JSON SHA256: 537bbf6304937a7e3864f38ffb0b41f2cd67492d76f5f1064688b8836ef66394

## Semantic gate

For every q in {1,2,4,7}:

- 4/4 fresh-process observations were exact;
- every q produced the same final output digest.

The frontier is therefore interpreted only after exactness.

## Coarse q surface

### q=1

- median normalized peak = 67,014,656 B
- median work time = 0.414408 s
- peak delta vs q1 = 0
- latency ratio vs q1 = 1.00000

### q=2

- median normalized peak = 67,024,896 B
- median work time = 0.400697 s
- peak delta vs q1 = **+10,240 B**
- latency ratio vs q1 = **0.966915**
- median latency reduction vs q1 ~= **3.31%**

### q=4

- median normalized peak = 71,217,152 B
- median work time = 0.392173 s
- peak delta vs q1 = **+4,202,496 B**
- latency ratio vs q1 = **0.946345**
- median latency reduction vs q1 ~= **5.37%**

### q=7

- median normalized peak = 71,507,968 B
- median work time = 0.388580 s
- peak delta vs q1 = **+4,493,312 B**
- latency ratio vs q1 = **0.937676**
- median latency reduction vs q1 ~= **6.23%**

## Pareto result

Observed two-objective Pareto q set:

```text
{1,2,4,7}
```

No tested q is strictly dominated on both:

- median peak;
- median latency.

This is exactly why one universal scalar "best q" would be misleading.

## Strong coarse observation

q=2 is a notable knee candidate in this implementation.

Relative to q=1 it buys about:

- 3.31% lower median work time;
- for only +10 KiB median normalized peak.

The next latency gains require much larger additional peak residency:

- q=4 adds about 4.01 MiB versus q1;
- q=7 adds about 4.29 MiB versus q1.

This does not make q=2 universally optimal.

It makes q=2 a strong **memory-efficient operating-point candidate** for the
current hosted workload.

## Unexpected physical result

The logical model predicted much larger simultaneous lane-byte differences.

Measured VmHWM compressed those differences strongly:

- q=1 -> q=2 was nearly free at the process-peak level;
- q=4/q=7 exposed only ~4-4.5 MiB additional normalized peak.

This is a valuable reminder:

```text
logical live bytes != process peak measurement
```

The runtime/allocator/numerical temporary frontier matters.

## Claim ceiling

**HOSTED_NUMPY_GROUPED_RESIDUE_CONCURRENCY_SWEEP**

## Next

B470 should turn the observed Pareto surface into a budget-aware governor rule.

Example shape:

- minimum-memory constraint -> q=1;
- small extra peak headroom -> q=2;
- larger headroom and lower-latency preference -> q=4 or q=7.

The rule must remain constraint/Pareto based rather than claiming one universal q.
