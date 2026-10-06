# FR-P9-010 — Physical phase-overlap residency

## Question

FR-P9-009 showed that a kernel-enforced memory quota can invalidate a high-concurrency plan and force a lower-concurrency replan. FR-P9-010 asks a different question: **can the same four-worker class survive if we change only the physical lifetime overlap of phase state?**

## Frozen two-phase proxy

Each worker executes the same semantic phases in both modes:

1. materialize and touch a private 16 MiB phase-A workspace;
2. process the same deterministic capability and job set;
3. emit the same phase-A workspace signature and job digests.

The physical schedule differs:

- `KEEP_WARM`: materialize the 8 MiB private capability **before READY**, overlapping it with the phase-A workspace;
- `FAULT_IN`: reach READY with only the phase-A workspace, explicitly unmap that workspace at the phase transition, then materialize the capability just in time.

This makes the experiment about **simultaneous lifetime overlap**, not about dropping semantic work.

## Quota derivation

Both four-worker modes are measured twice under a 256 MiB high quota. The tight quota is derived only when the measured peak gap is at least 8 MiB and is chosen strictly between:

```text
max(FAULT_IN peaks) < tight quota < min(KEEP_WARM peaks)
```

If the hosted runner does not expose that separation, the experiment fails closed.

## Required result

Under the *same* four-worker count and *same* kernel `memory.max`:

- `KEEP_WARM` must trigger isolated cgroup OOM;
- `FAULT_IN` must complete with zero OOM kills;
- phase-A signatures and all deterministic job digests must match the high-quota baseline.

## Interpretation boundary

A PASS would show only that this hosted Linux proxy has a real phase-overlap residency effect large enough to change quota survival. It would **not** prove that FAULT_IN is universally better. The latency/coordination tax is intentionally left as the next falsifier.

Decision candidate:

`TREAT_PHASE_LIFETIME_OVERLAP_AS_A_PHYSICAL_RESIDENCY_VARIABLE;FAULT_IN_AFTER_RELEASE_CAN_PRESERVE_THE_SAME_CONCURRENCY_CLASS_UNDER_A_QUOTA_WHEN_KEEP_WARM_OVERLAP_CANNOT`

Claim ceiling:
`HOSTED_GITHUB_LINUX_CGROUP_V2_PHASE_OVERLAP_AND_HASHING_PROXY_ONLY_NO_UNIVERSAL_RESIDENCY_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM`
