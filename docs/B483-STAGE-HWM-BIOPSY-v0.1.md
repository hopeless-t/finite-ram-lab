# B483 — Stage HWM/RSS Biopsy v0.1

Status: **DESCRIPTIVE STAGE LOCALIZATION AFTER CONFIRMED CONTENT EFFECT**.

## 1. Goal

B482 established that pre-materialized equal-size input contents can produce a
repeatable work-phase HWM difference.

B483 asks:

> At which numerical stage does the HWM trajectory first diverge?

The purpose is localization, not yet mechanism proof.

## 2. Milestones

Every fresh child records both VmHWM and current VmRSS at:

1. pre-load;
2. post-load;
3. post-accumulator allocation;
4. after each residue-lane production;
5. after each CRT lane fold;
6. after each group release + GC;
7. after final centering.

All HWM values are also normalized to pre-load HWM.

RSS is stored as signed delta from pre-load RSS.

## 3. Physical design

Same B482 content-isolation contract:

- pre-materialized content474/content476;
- q2 and q4;
- eight independent hosted-runner blocks;
- two replicates per condition;
- order + reverse order.

Total measured children:

`64`.

## 4. Confirmatory gate

Only the final HWM effect is confirmatory.

Per q:

- content476 final HWM growth < content474 final HWM growth.

Two tests use Holm familywise alpha 0.05.

Only after the final effect replicates is the milestone trajectory interpreted.

## 5. Stage localization rule

For each q, B483 reports the first milestone where:

- all 8 runner blocks have a negative content476-content474 HWM delta;
- median magnitude is at least one 4096-byte page.

The same descriptive rule is also applied to current RSS.

This "first unanimous divergence" is a biopsy target, not a causal proof.

## 6. Why HWM and RSS are both needed

HWM answers:

> Which stage first creates the persistent process high-water difference?

Current RSS helps distinguish:

- a live-residency difference at that milestone;
- a historical HWM difference after the live states have converged.

## 7. Claim ceiling

**DESCRIPTIVE_STAGE_HWM_BIOPSY**

Multiple milestone searches are intentionally not promoted to confirmatory
p-values. The selected first stage must be tested independently in the next
bounce.

## 8. Next

B484 should isolate the first localized stage in a minimal child:

- run only the required preconditions;
- execute the target primitive once;
- stop immediately;
- compare content474/content476 across fresh runner blocks.

That is the causal-bite path from trajectory localization to a primitive-level
mechanism.
