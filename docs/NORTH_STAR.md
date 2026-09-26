# North Star

> **Status:** FROZEN DIRECTIONAL PRINCIPLE  
> **Scope:** This document guides research direction. It does not authorize a specific implementation.

## 1. North Star

Finite RAM Lab seeks to determine how closely finite physical RAM can be aligned with actual application memory demand, and whether better coordination between application-local knowledge and operating-system-global knowledge can move the practical memory limit without unacceptable performance loss.

The project is not committed in advance to a custom kernel, a userspace controller, or any particular mechanism.

The research direction is:

> Observe the application/OS information gap, measure its cost, and only then choose the smallest mechanism capable of closing the bottleneck.

## 2. Capability, not product

The desired capability is:

    application-local intent
            +
    OS-global pressure/state
            ↓
    evidence-grounded coordination
            ↓
    better finite-RAM allocation

This capability may eventually be implemented as:

- no new mechanism, if existing Linux behavior is already sufficient;
- an application-facing hint/contract library;
- a userspace memory coordination agent;
- a hybrid userspace + existing-kernel-interface design;
- a minimal kernel extension;
- a custom kernel policy only if the evidence requires it.

The implementation is an experimental result, not a premise.

## 3. Preferred escalation order

When an observed bottleneck is found, prefer the least invasive mechanism that can test the hypothesis:

    existing observation interfaces
        ↓
    existing userspace control/advice interfaces
        ↓
    userspace coordination prototype
        ↓
    hybrid userspace + kernel hooks
        ↓
    minimal kernel change
        ↓
    custom kernel policy

Skipping directly to a deeper layer requires evidence that the shallower layer cannot express, observe, or execute the needed decision with acceptable latency and overhead.

## 4. Why userspace coordination is a serious candidate

Applications possess information the kernel often cannot infer directly, such as:

- semantic phase transitions;
- regenerable caches;
- reclaimable regions;
- recovery cost;
- latency sensitivity;
- near-future demand.

The operating system possesses information individual applications do not, such as:

- global physical-memory pressure;
- competition between processes;
- reclaim activity;
- faults and refaults;
- swap and I/O pressure;
- system-wide resource constraints.

A coordination layer could combine these complementary views without replacing kernel authority.

The intended authority split is:

    Application
      provides intent / semantics / proposals

    Coordination layer
      combines information and proposes bounded actions

    Kernel
      retains enforcement and physical-resource authority

Application hints are not commands.

## 5. Observation remains first

The current project phase remains observation-only.

No coordination layer is authorized until experiments identify a reproducible bottleneck that can plausibly be reduced by additional information or coordination.

Candidate bottleneck classes include:

- fundamental capacity shortage;
- application/OS information gap;
- residency mismatch;
- reclaim timing;
- stale or missing demand information;
- control latency;
- swap or I/O cost;
- another mechanism discovered by measurement.

## 6. What the project may eventually produce

Possible research outputs include:

1. **Memory Observation Plane**  
   A synchronized application/OS event model for memory-demand and memory-pressure analysis.

2. **Bottleneck Taxonomy**  
   Reproducible classifications of why performance collapses under finite RAM.

3. **Value-of-Information Map**  
   Measurements of how much particular application-side signals improve decisions.

4. **Memory Coordination Contract**  
   A typed protocol for exchanging memory intent, pressure, reclaimability, recovery cost, and state transitions.

5. **Memory Coordination Agent**  
   A userspace prototype that coordinates applications and existing Linux memory controls.

6. **Kernel Extension**  
   Only if required by missing observability, insufficient control granularity, unacceptable latency, or excessive userspace overhead.

7. **Negative Result**  
   Evidence that a proposed coordination mechanism is unnecessary or ineffective is a valid project outcome.

## 7. Transfer value outside this repository

Finite RAM Lab is a systems research project, not an MVCA implementation.

However, architectural lessons may later be transferred elsewhere if they survive experiment.

Potential transferable ideas include:

- observation before decision;
- proposal versus authority;
- local knowledge versus global coordination;
- typed state transitions;
- bounded actions and budgets;
- stale-state detection;
- feedback-driven control loops;
- explicit evidence/decision separation;
- failure-safe fallback when coordination information is missing.

Such transfer is secondary and must not change experimental claims inside Finite RAM Lab.

## 8. Decision rule for future architecture

When evidence identifies a bottleneck, choose architecture by asking:

1. What information is missing?
2. Who currently owns that information?
3. What action is required?
4. Can existing Linux interfaces express that action?
5. Is userspace latency sufficient?
6. What is the smallest trusted component that must gain authority?
7. What failure mode appears if the coordinator is wrong, stale, or unavailable?

Only then decide between:

    application library
    userspace bridge
    hybrid controller
    kernel extension
    custom kernel policy

## Principle

> **Do not choose the control plane before measuring the coordination gap.**

The North Star is not "build a new kernel."

The North Star is:

> **Use evidence to discover the smallest mechanism that aligns finite RAM supply with actual application demand.**
