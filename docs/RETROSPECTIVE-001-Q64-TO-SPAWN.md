# RETROSPECTIVE-001 — From 777 to deliberate Q64-state construction

> **Status:** RESEARCH PAUSE / SYNTHESIS
> **Cut:** after MEMCG-005G-C v2 run 36595481746
> **Purpose:** distinguish what survived, what died, and what the lab actually learned.

## 1. Where we started

The early observation was visually seductive:

- 64-page / 256 KiB steps;
- a separate pressure knee around 80-88 MiB;
- repeated rare zero-delta / delayed-Q64 specimens.

The first temptation was to connect them into one compact story.

That story was wrong.

The most important early success was not confirming a hypothesis.
It was separating phenomena that only looked related.

## 2. 777 / K7 direct-cause hypothesis died

The original 777-style direct causal explanation did not survive controlled tests.

What survived independently:

- Q64 = 64 base pages = 256 KiB on 4 KiB pages;
- pressure knee 80 < K <= 88 MiB.

They remain real observations, but no longer share an assumed direct causal chain.

Method lesson:

`coincidence in scale != shared mechanism`

## 3. Q64 became source-grounded

Linux source supplied the first hard anchor:

`MEMCG_CHARGE_BATCH = 64`

and the charge path:

`try_charge_memcg -> consume_stock/refill_stock`

MEMCG-004 then reproduced the staircase:

- fresh Q64;
- residual 63;
- 63 stock-consuming touches;
- next Q64.

At this point Q64 stopped being a mysterious empirical number.

It became an observable projection of a per-CPU charge-stock state machine.

## 4. Natural rare specimens were not a single geometric tail

G-A biopsy:

- 28 exact-zero specimens;
- depth1 = 22/28;
- deeper depths at 14, 34, 45, 45, 47, 48.

A single geometric residual-depth model failed badly.

That forced the next conceptual shift:

`rare event frequency`

was less informative than

`hidden state at capture`.

## 5. Controlled bait arithmetic emerged

Once a fresh Q64 is observed, batch arithmetic gives a concrete state variable.

If the primer consumes page 1 of a 64-page batch:

- residual is 63;
- controlled additional consumption should place the system at a chosen residual depth.

This yielded b-values mapping to observed depths and the b63 depth1 construction.

At this stage the rare Pokémon stopped being purely a search problem.

It became a possible state-construction problem.

## 6. Capacity signal appeared — then we attacked our own explanation

G-B showed a very large CAP8 vs CAP70 difference.

Later panels ruled out a simple 64-page threshold.

Dense G-F localized a strong transition around T10.

Then MATH-008 found a devastating confound:

- 8/9 were one decimal digit;
- 10+ were two digits.

The correct response was not to defend T10.

We designed a same-capacity textual intervention:

- 8 vs 08;
- 9 vs 09.

G0 Stage A then showed:

- padding did not raise capture;
- capacity-associated signal remained strong.

This was one of the most important methodological moments in the project:

**a promising result survived an adversarial alias breaker.**

## 7. PTE went from speculation to a connected mechanism

Linux v7.0 source connected:

`GFP_PGTABLE_USER (__GFP_ACCOUNT)`
-> `__memcg_kmem_charge_page`
-> `try_charge_memcg`
-> `consume_stock`

and anonymous fault ordering showed:

`pte_alloc` before data-page allocation.

G0 then observed the mechanism's signature:

- VmPTE +4 KiB appeared only in H32;
- LOW PTE-growth specimens were 5/5 Q64;
- exact-zero was absent in those five.

The original naive 8-vs-10 2 MiB-boundary story remained too small.

But H32's larger footprint produced a boundary incidence of the right order.

The model evolved into two components:

1. a capacity-associated trigger near the 10-page region;
2. a larger-footprint PTE suppressor.

## 8. The first natural-state discriminator worked

G0's failure-only second touch turned exact-zero specimens into state biopsies.

19 LOW exact-zero specimens:

- 12 -> next Q64 = R1 candidate;
- 7 -> next zero = deeper residual state.

That connected the historical depth1 dominance to a prospective state readout.

## 9. Evidence handling became part of the research object

The lab also learned that experimental validity is not enough if artifacts expire.

EVIDENCE-RESIDENCY v1 established:

`HOT -> WARM -> COLD -> RESTORE -> VERIFY`

G0:
- 17/17 Drive archives byte-identical.

Controlled-spawn v2:
- 9/9 Drive archives byte-identical.

This is finite-ram-lab dogfooding its own residency principles on research evidence.

## 10. Controlled spawn changed the nature of the problem

The decisive design move was:

- allocate the PTE table on preparation CPU P;
- migrate to stock CPU S;
- observe a fresh Q64 on S;
- count exact post-primer consumption;
- measure a target phase.

This separates:

- page-table setup;
- unknown initial stock;
- controlled post-primer stock.

Pilot result:

- 72 frozen candidates;
- 55 directly observed primers;
- **55/55 terminal phase patterns matched**.

b63:

- **14/14 primer-qualified trials produced ZERO -> Q64**.

The strict frozen endpoint remained lower because negative accounting deltas were classified as failures.

The scientific bottleneck has therefore moved.

Before:

`Can the rare state be predicted?`

Now:

`Can the clean primer/reset condition be acquired and observed reliably without accounting interference?`

## 11. The -17 discovery is not a disappointment

17 calibration failures all had exactly:

`delta = -17 pages`

and several bait-stage negative deltas did not alter the eventual stock phase.

Linux source confirms stock drainage can uncharge an arbitrary cached page count as one negative memory.current step.

The exact source of -17 is not yet proven.

But it demonstrates an important distinction:

`memory.current delta != measured data-page charge in every instant`

The instrumentation itself now has a known interference class.

That is progress.

## 12. What is now high-confidence

### Strong

- Q64 is a memcg batch/stock phenomenon.
- stock is per-CPU and usable as a controllable hidden-state variable.
- PTE allocation can consume that same stock.
- target-time PTE allocation can be removed by preconditioning.
- after an observed Q64 reset, page-count arithmetic predicts b62/b63/b64 terminal phase with very high consistency.
- argv decimal width is not the T10 explanation.
- capacity-associated natural-state signal is real enough to survive the direct alias breaker.

### Moderate / needs more work

- exact shape of the natural capacity response around 9-12 pages.
- mechanism producing the capacity trigger near 10.
- H10/H32 non-monotonicity decomposition.
- exact source of the -17 uncharge signature.
- transfer from hosted Ubuntu kernel behavior to other machines/kernels.

### Rejected / downgraded

- 777/K7 direct cause.
- one geometric residual-depth population.
- simple 64-capacity threshold.
- decimal argv-width explanation.
- naive 8->10 crossing of a uniform 2 MiB PTE boundary.
- small-mTHP explanation for the observed hosted runs.

## 13. Methodological lessons

### A. Counter-hypotheses paid off

The argv-width audit could have destroyed the T10 result.

That made it worth doing.

### B. Source + experiment beat either alone

Source exposed Q64 and PTE plausibility.

Experiment established when those paths actually mattered.

### C. Measure state transitions, not only outcomes

VmPTE, second-touch biopsy, CPU receipts and exact deltas were more valuable than collecting another large panel of endpoint counts.

### D. Preserve strict endpoints even when a better interpretation appears later

49/72 remains the frozen controlled-spawn endpoint.

55/55 is a separate post-primer mechanistic observation.

Keeping both prevents hindsight from rewriting the experiment.

### E. Once a rare event is constructible, natural incidence becomes a different question

Natural capture rate and controlled construction reliability are no longer the same research target.

That is the major conceptual transition of the project.

## 14. Strata cross-check

External intake:
`docs/STRATA-001-EXTERNAL-INTAKE.md`

Strata independently embodies several patterns the lab has been converging on:

- HOT/WARM/COLD placement across VRAM/RAM/SSD;
- dynamic expert residency;
- prior hotness + online adaptation;
- borrowing expert-cache capacity for prompt scratch and returning it later;
- bounded pinned-memory staging;
- physical I/O reorder/dedup;
- bottleneck shifts after cache saturation;
- cases where adding a slower device makes the whole system worse.

This is not evidence for the memcg mechanism.

It is evidence that the broader finite-resource design principles discovered here are useful in a real rapidly evolving AI runtime.

## 15. Where to resume after the pause

Do not immediately launch anything.

Candidate next questions, after Human review:

1. identify the -17 source and redesign the observer so uncharge noise is separated from touch charge;
2. improve primer acquisition while preserving observed-reset semantics;
3. run a fixed-N b63 reliability test only after the observer is clean;
4. separately return to the natural 9-12 capacity onset;
5. turn Strata-derived leaseable-residency / staging-knee patterns into isolated finite-ram-lab experiments.

The project has crossed a boundary:

**from finding rare memory behavior to engineering memory-state transitions.**
