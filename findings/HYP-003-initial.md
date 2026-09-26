# HYP-003 Initial Finding

> **Status:** BOUNDED INFORMATION MISMATCH SUPPORTED / REUSE COST SUPPORTED  
> **Run:** 36247200797

## Question

Under 160–162 MiB memcg pressure, does residency follow the independently controlled initial fault/touch order even when future semantic HOT demand is assigned independently, and does conflict between those signals increase reuse cost?

## Execution

All frozen execution checks passed:

- 16 independent runner blocks;
- 128 total factorial trials;
- all cells complete;
- all trials PASS;
- no OOM;
- content integrity preserved;
- future HOT assignment was not used before the primary residency snapshot.

## Manipulation check — fault order

Runner-block mean:

    resident(second-faulted) - resident(first-faulted)
    = +0.088012

Exact one-sided sign-flip:

    p = 1.5259e-05

Cluster-bootstrap 95% interval:

    [+0.064801, +0.116629]

The CHAR-002 fault-order effect reproduced in the same shared-VMA substrate used for the semantic test.

## Primary result — semantic residency gap

Primary estimand:

    HOT resident fraction when HOT == second-faulted
    minus
    HOT resident fraction when HOT == first-faulted

Observed runner-block mean:

    +0.083124

Exact one-sided sign-flip:

    p = 0.00209045

Cluster-bootstrap 95% interval:

    [+0.034279, +0.132578]

The future-needed region was materially more resident when future semantics happened to align with the historical fault-order cue.

Because future HOT identity was independently assigned and unused before the snapshot, this is direct evidence that past fault/touch history and future application demand are separable signals in this bounded workload.

## Key secondary result — cost of semantic conflict

Runner-block geometric mean HOT-retouch latency ratio:

    misaligned / aligned = 77.83x

Exact one-sided sign-flip:

    p = 9.1553e-05

Cluster-bootstrap 95% ratio:

    [21.22x, 231.40x]

The mismatch therefore carried a large measured reuse cost under the declared pressure conditions.

## Pressure-level diagnostics

### 160 MiB

    mean fault-order residency contrast = +0.11950
    mean HOT fraction aligned           = 0.95026
    mean HOT fraction misaligned        = 0.82483
    HOT-not-fully-resident rate aligned = 0.25
    HOT-not-fully-resident rate mismatch= 1.00
    median retouch aligned              = 0.734 ms
    median retouch misaligned           = 257.304 ms

### 162 MiB

    mean fault-order residency contrast = +0.05652
    mean HOT fraction aligned           = 0.94725
    mean HOT fraction misaligned        = 0.90643
    HOT-not-fully-resident rate aligned = 0.21875
    HOT-not-fully-resident rate mismatch= 0.96875
    median retouch aligned              = 0.667 ms
    median retouch misaligned           = 169.917 ms

## Interpretation

The evidence chain now supports a bounded information-gap statement:

    historical fault/touch order
              ↓
    later residency selection

while

    future semantic HOT demand

is independently assigned by the application.

When the future need conflicts with the historically favored residency state, the needed region is less resident and future reuse is much slower.

This is not merely a correlation assembled across different experiments: HYP-003 orthogonalized the historical cue and future semantic identity inside the same factorial experiment.

## Relationship to prior studies

CHAR-002 established that initial fault/touch order can steer later residency.

HYP-003 now shows why that matters to the research North Star:

> the OS-visible historical cue and the application's future-demand information can disagree, and that disagreement can be expensive.

## What this does not establish

HYP-003 does not show:

- that Linux is globally wrong to use historical state;
- the exact kernel data structure responsible;
- that an application hint is safe or beneficial;
- that a coordinator should be built;
- that the measured latency ratio generalizes beyond this hosted memcg workload;
- the production Value-of-Information of any specific signal.

## Council consequence

The previous pause on formal Value-of-Information analysis can now be lifted.

The next research stage should quantify **decision headroom** before selecting another control mechanism.

The calculation must keep separate:

- opportunity frequency;
- cost when the historical cue and future demand disagree;
- achievable oracle improvement under a declared decision model;
- harm from wrong/stale semantic information.

EXP-002's wrong-hint harm remains an essential constraint.

## Authority boundary

HYP-003 establishes a bounded, same-experiment application/OS information mismatch with measured performance cost.

It authorizes formal Value-of-Information / decision-headroom analysis, not a coordination architecture.
