# Strata Derivative Family Intake — 2026-10-03

Status: SOURCE-GROUNDED DERIVATIVE FAMILY MAP / NO BENCHMARK NORMALIZATION

Purpose: treat the emerging Strata derivative ecosystem as a family of natural experiments in finite residency rather than interchangeable forks.

Raw tokens/sec are not compared across different machines, models, quantizations, contexts, or operating systems.

## Family thesis

Several derivatives deliberately move the boundary between VRAM, host RAM, shared host memory, SSD/NVMe, precision, prompt buffers, KV/session state, and multi-GPU execution.

This gives Finite RAM Lab a natural experiment family: same broad inference problem, different residency / precision / topology decisions, different pressure knees and failure domains.

## 1. strata-nvfp4

Repository: sergqwer/strata-nvfp4
Observed head: 69a60f53914f92871b883e826fbb871949d30c15

Architectural mutation:
- ModelOpt NVFP4 routed experts instead of upstream Q2/Q3-style packs.
- About 63 GiB routed experts for the baseline pack described by the fork.
- File tier for lower-RAM systems.
- Hottest non-VRAM experts pinned in RAM; colder experts read from SSD.
- Adaptive VRAM expert re-ranking.
- Elastic KV allocation instead of paying full max-context KV cost at startup.
- Multiple precision-preserving alternatives for embeddings, PLE, KV, prompt arithmetic, and expert packs.

Finite RAM interpretation:
precision is itself a residency tier. More bits can buy semantic quality while increasing RAM, VRAM, disk, or bandwidth pressure.

Useful objective: minimize residency and movement cost subject to quality, task-survival, and tail-latency constraints.

## 2. strata-glm

Repository: sergqwer/strata-glm
Observed head: ed37419fccd0c52e07d26d526a29c2098f547843
Declared status: archived experiment

Architectural mutation:
- Moves Strata-style tiering to GLM-5.3-Flash NVFP4.
- Roughly 204 GB MoE checkpoint described by the derivative.
- One RTX 5090 + 128 GB RAM + two NVMe drives in its documented reference host.
- Static hot VRAM tier, pinned-RAM cache, disk-only experts, prediction-based prefetch, mirrored SSD copies, unbuffered reads, lazy context caches.
- Offline cache simulation used before building policy changes.

Especially valuable negative evidence:
- Fully exclusive RAM/VRAM tiers were rejected.
- CPU execution of part of RAM experts was rejected.
- Direct disk-to-VRAM staging was rejected.
- Lossless expert compression was ineffective.
- 3-bit experts were rejected on quality.
- Deeper speculative prefetch did not remove the movement wall.

Finite RAM interpretation:
adding backing capacity helps only while movement and miss latency stay inside the semantic deadline.

## 3. webpolis/Strata

Repository: webpolis/Strata
Observed head: 7cc166ea67ddd223d6be25668a89b3de8f54ee8f
Fork parent: Niko1221/Strata

Architectural mutation:
- Spare NVIDIA GPUs become additional expert-cache / compute tiers.
- Layer-split pipeline parallelism gives each GPU a contiguous layer range and its own expert cache.
- A token crosses GPU boundaries once per verify window rather than per layer.

Important negative result:
a sufficiently slow extra GPU can make a faster pair worse.

Finite RAM interpretation:
more nominal capacity is not monotonic useful capacity. Capacity must be topology weighted by bandwidth, latency, synchronization, and tail behavior.

## 4. Strata-Lanes

Implementation repository: rhgo1749/Strata-Lanes
Observed head / operational pin: 4b5b47d6e50250b71c52fe4fe7d33593684dce91
Recipe: rhgo1749/qwen3.8-flash-next-strata-gpu-per-lane-recipe

Architectural mutation:
- One independent inference lane per GPU.
- Multiple lane processes physically share one large host-RAM expert arena.
- GPU cache, KV/session state, speculative state, CUDA state, and generation loop remain lane-local.
- Strict session affinity is used because moving a continuing conversation destroys locality and can force a large re-prefill.

Finite RAM interpretation:
information obligation does not imply duplicated resident representation.

A second invariant follows: load balancing does not imply state-locality-preserving scheduling.

## 5. spideytznn/Strata

Repository: spideytznn/Strata
Observed head: 0c824e173f0873993b5fd83db570c03537127ac0
Declared upstream basis: d9ab8435f654c368c586340d490915f6addf56a3

Architectural mutation:
- Independent prefill buffer selection using remaining VRAM only when configured reserve remains intact.
- Does not evict experts merely to manufacture prefill-buffer space.
- Coordinates resident-expert RAM budgeting with conversation-cache budgeting.

Finite RAM interpretation:
two subsystems cannot independently spend the same headroom.

Candidate invariant: available global headroom is not the sum of each subsystem's locally perceived free headroom.

## 6. StrataGP

Repository: gputier/StrataGP
Observed head: 236388d66c0f6790504a861239a899814527e062
Fork parent: Niko1221/Strata

Current main intentionally keeps a small set of separable changes on a recent upstream base.

Relevant additions include:
- prompt tokenization caching with identical token IDs;
- parity-test improvements;
- API-key validation;
- read-only GGUF-directory tolerance.

Finite RAM interpretation:
validated prefix reuse is a sufficient-state / reuse experiment rather than primarily a tiering experiment.

## Family comparison

| derivative | main changed resource | Finite RAM target |
|---|---|---|
| upstream Strata | RAM/VRAM/SSD expert hierarchy | base tiered residency |
| strata-nvfp4 | precision + elastic KV + stronger SSD tier | quality-constrained residency |
| strata-glm | extreme RAM/VRAM/NVMe pressure | bandwidth / miss deadline |
| webpolis/Strata | extra GPUs / layer split | topology-aware capacity |
| Strata-Lanes | shared host arena + independent lanes | representation sharing / state locality |
| spideytznn/Strata | prompt buffers + conversation/expert budgets | global headroom / double counting |
| StrataGP | prefix reuse / parity | sufficient-state reuse |

## Frozen hypotheses

1. PRECISION_IS_A_RESIDENCY_TIER
2. HEADROOM_IS_GLOBALLY_CONSERVED
3. CAPACITY_IS_TOPOLOGY_WEIGHTED
4. SHARED_REPRESENTATION_CAN_BEAT_REPLICATED_RESIDENCY
5. STATE_LOCALITY_IS_PART_OF_SEMANTIC_SURVIVAL
6. TIERING_EVENTUALLY_HITS_A_MOVEMENT_WALL

## Proposed STRATA-FAMILY-001

Do not compare raw author-reported tokens/sec.

Normalize each architecture into:
- resident bytes by tier;
- immutable shared bytes;
- lane-local bytes;
- bytes moved per token/request;
- miss probability and miss latency;
- background headroom;
- semantic quality proxy;
- current-task survival;
- reconstruction/re-prefill bytes;
- control transitions;
- p95/p99 latency.

Candidate policy classes:
- ALL_RAM_BASELINE
- PRECISION_DOWNSHIFT
- SSD_BACKED_EXPERTS
- EXTRA_GPU_CACHE
- SHARED_HOST_ARENA
- COORDINATED_MULTI_BUDGET
- PREFIX_STATE_REUSE
- COUPLED_RESOURCE_ORACLE

The goal is not a universal winner. The goal is to identify the phase boundaries where each architectural idea becomes beneficial or harmful.

Transfer rule:
transfer invariants aggressively; transfer thresholds conservatively; transfer benchmark numbers only with their exact environment; re-prove target behavior locally.

Claim ceiling: SOURCE_GROUNDED_STRATA_DERIVATIVE_FAMILY_MAP_ONLY
