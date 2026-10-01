# B482 — Pre-materialized Input Isolation Receipt

Status: **PASS / CONTENT EFFECT REPLICATED**

## Frozen execution

- workflow run: 36939052146
- aggregate job: 110626217625
- execution head: 4c11cfd374935809840035d452ea9a572a2ca43a
- tests: 4/4 PASS
- runner blocks: 8
- measured child observations: 64
- aggregate artifact ID: 11199017989
- artifact ZIP SHA256: 97a1bd1b21aca29534d591520f635e8ed05bb0fbe137b35cc8f2d6a9b59c52f3
- aggregate JSON SHA256: 7fd6b476c2fcbfad0d04c605b15c9aca4c7c65638b5baacb776e43b54831b5d0

## Isolation boundary

Seed474 and seed476 inputs were generated in the runner-block parent process and
serialized as equal-size raw int64 files.

The measured child:

- did not instantiate the RNG;
- loaded both variants through the same `np.fromfile` path;
- observed zero seed/content difference in load-phase HWM growth in all blocks.

Thus the previous effect is not explained by RNG generation inside the measured
process.

## q2

Content476 - content474:

- median load-phase delta = **0 B**
- median work-phase delta = **-135,168 B**
- median total-growth delta = **-135,168 B**
- median absolute work-HWM delta = **-135,168 B**

Confirmatory signs:

- work lower 8/8 blocks
- total lower 8/8 blocks
- p=0.00390625 for both
- Holm significant

Classification:

**PREMATERIALIZED_CONTENT_EFFECT_REPLICATED**

## q4

Content476 - content474:

- median load-phase delta = **0 B**
- median work-phase delta = **-135,168 B**
- median total-growth delta = **-135,168 B**
- median absolute work-HWM delta = **-139,264 B**

Confirmatory signs:

- work lower 8/8
- total lower 8/8
- p=0.00390625
- Holm significant

Classification:

**PREMATERIALIZED_CONTENT_EFFECT_REPLICATED**

## Scientific interpretation

Under the current hosted NumPy implementation, equal-size input contents induce a
repeatable difference in the measured numerical work-phase process high-water
memory.

This is surprising because the array shapes and declared dtypes are fixed.

Therefore the result should not yet be promoted into a production workload model
without identifying the stage that creates the difference.

Potential classes include:

- residue-production temporary behavior;
- CRT-fold temporary behavior;
- allocator/page-residency interaction;
- another implementation-specific content-sensitive path.

No specific mechanism is claimed by B482.

## Next

B483 should instrument HWM/current-RSS milestones around:

1. input load;
2. accumulator allocation;
3. each residue-lane production;
4. each CRT fold;
5. each group release.

The first milestone where the content474/content476 trajectories diverge should
be targeted for the next causal biopsy.
