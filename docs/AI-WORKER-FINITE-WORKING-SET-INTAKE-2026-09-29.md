# AI Worker Finite Working-Set Intake — 2026-09-29

> **Status:** RESEARCH INTAKE / NON-AUTHORITATIVE
> **Execution authority:** NONE
> **Purpose:** Translate external primary-source observations about AI context management into falsifiable Finite RAM Lab hypotheses without claiming that LLM context and physical RAM are the same mechanism.

## Primary sources

1. Strands Agents — Context management  
   https://strandsagents.com/docs/user-guide/sdk/context-management/
2. Strands Agents — Built-in context-management modes  
   https://strandsagents.com/docs/user-guide/concepts/context-management/built-in-modes/
3. Strands Agents — Context Offloader  
   https://strandsagents.com/docs/user-guide/concepts/plugins/context-offloader/
4. OpenAI — Tool search  
   https://developers.openai.com/api/docs/guides/tools-tool-search
5. Sim, Eiger, Kohno (2026), *AI-Enabled Human Memory Manipulation: Misleading AI-Generated Summaries Distort Human Memory*  
   https://arxiv.org/abs/2609.28820
6. Tabelog Tech Blog — AI requirements-definition workflow using staged/priority-tagged questions  
   https://tech-blog.tabelog.com/entry/ai-requirements-definition-with-questions
7. Cloudflare — *Introducing cf: the agentic CLI for the entire Cloudflare API*  
   https://blog.cloudflare.com/cloudflare-cf-cli-launch/
8. GPT Researcher — commit-pinned Jev context-filter implementation and evals  
   https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/gpt_researcher/context/jev_filter.py  
   https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/evals/context_filter/README.md
9. Claude / claude.dev — *Automating eval design and hillclimbing with Claude*  
   https://claude.dev/blog/automating-eval-design-and-hillclimbing/

## Source observations

### S1 — Large context items can be offloaded rather than destroyed

Strands documents a context stash that stores message content before context-reduction strategies act. Its context offloader can replace a large tool result with a preview plus references and retrieve the full content later.

**Observed system property:**

```text
active context copy
!=
canonical retrievable content
```

The public docs also describe an auto strategy that truncates large tool results around a configured threshold and summarizes older messages under context pressure.

### S2 — Truncation is explicitly lossy unless the original is retained elsewhere

Strands describes reactive truncation as lossy when the omitted middle content is not externally preserved. The offloader exists specifically to retain content outside the active context.

**Atomic distinction:**

```text
compress-and-retain-pointer
!=
truncate-and-forget
```

### S3 — Human memory can be altered by a misleading summary

The Sim/Eiger/Kohno study reports a controlled human-subject experiment in which exposure to a misleading AI-generated summary reduced accurate recall of a previously viewed event compared with an accurate-summary condition.

This is evidence about **human memory**, not LLM memory.

**Allowed transfer:** summaries can become an information-integrity hazard when a later actor relies on the summary instead of re-reading source material.

**Forbidden transfer:** the paper does not prove that LLM context compaction corrupts model state in the same cognitive mechanism.

### S4 — A large candidate set can be retained while only a small stage-relevant subset is active

Tabelog reports a practitioner workflow where AI-generated decision questions exceeded 50. Adding stage and priority tags reduced the questions that needed answers during requirements definition to 8.

**Observed workflow property:**

```text
total pending questions
>
currently resident decision set
```

The deferred questions were not equivalent to deleted questions.

### S5 — Tool definitions themselves can become a finite working-set problem

OpenAI Tool Search defers tool definitions and loads only the subset needed by the current request. This is not a RAM mechanism, but it supplies a concrete AI-runtime example where total available capacity and active resident description are intentionally separated.

### S6 — A 3,000-operation capability universe can stay addressable without being resident

Cloudflare's `cf` CLI is generated across more than 3,000 API operations, but the agent-facing discovery path uses `cf cli search` over a small search index. Cloudflare also makes JSON the default interface and explicitly frames compact machine-readable output as a context-saving measure.

**Observed system property:**

```text
addressable capability universe
!=
resident command description set
```

This is structurally analogous to virtual addressability versus physical residency, without implying the same mechanism.

### S7 — Evidence selection can be treated as a working-set problem

GPT Researcher's commit-pinned Jev path scores scraped chunks by question usefulness and keeps a bounded subset for context. Its evaluation harness compares Jev against embeddings and no filtering on recorded pages.

**Observed system property:**

```text
retrieved corpus
!=
resident evidence context
```

This creates a second AI-worker working-set domain beside tool schemas: evidence passages.

### S8 — Optimization needs held-out validation, not only lower footprint

Claude's eval/hillclimb guidance keeps one change only when both train and held-out test improve; regressions and train-only improvements are reverted. It also recommends against merging gains that remain within eval noise.

**Research consequence:** a smaller active working set is not a success criterion by itself. Any future AI-worker controller must measure task quality and held-out regressions alongside token or latency reduction.

## Atomic decomposition

### A1 — Capacity != residency

Let:

- (U) = total available state/information/capability universe;
- (R_t) = active resident working set at time (t);
- (B_t) = active resource budget;
- (q_t) = current task/query.

Candidate abstraction:

```text
R_t = Select(U, q_t, B_t, control_state_t)
```

The research object is not only how large (U) is. It is how (R_t) is selected, retained, evicted, and restored.

### A2 — Eviction policy and restore fidelity are separate variables

Two systems may expose the same active footprint while differing radically in recoverability.

```text
small active state + exact/page-in restore
!=
small active state + irreversible lossy summary
```

Candidate metrics therefore need both:

- active footprint;
- restore fidelity / source recoverability.

### A3 — Semantic hotness matters more than age alone

Possible AI-worker analogues to the existing Finite RAM classes:

| Finite RAM class | AI-worker analogue |
| --- | --- |
| PERSISTENT_HOT | authority constraints, invariant contract, current objective |
| SESSION_HOT | active reasoning state, current task facts |
| PHASE_HOT | temporary tool output, intermediate calculation |
| STREAM_COLD | one-shot retrieved material already reduced into durable evidence |
| REUSABLE_WARM | prior decisions/evidence likely to be retrieved again |

This is a mapping hypothesis, not an identity claim.

### A4 — Source pointers can function like recoverable backing storage

A summary that replaces source material without a durable pointer is analogous to an irreversible lossy transform, not ordinary paging.

Candidate invariant:

```text
Compacted Working State != Canonical Source State
```

A governed AI worker should be able to distinguish:

- content still resident verbatim;
- content represented by a reversible reference;
- content represented only by a lossy summary;
- content discarded.

### A5 — Selection policy and authority policy are different variables

The same item can be:

- available but not resident;
- resident but not selected;
- selected but not authorized;
- authorized but not yet used.

This matters when the working-set object is a tool rather than passive evidence.

```text
residency decision
!=
execution authority
```

Finite RAM Lab should model this only as a cross-domain control distinction; authority semantics belong to MVCA / tool-surface research.

### A6 — Prefetch depth is an optimization variable

The finite-working-set model predicts a tradeoff:

```text
too little prefetch -> latency / stalls
too much prefetch   -> pressure / wasted residency
```

Start future experiments at bounded prefetch depth rather than assuming maximum speculative context is useful.

## Cross-domain working hypothesis

> Performance under finite resources may depend less on total available capacity than on whether the minimum task-relevant subset is resident at the right time and can be restored without semantic corruption.

This hypothesis applies structurally across:

- physical page residency;
- LLM context;
- tool schemas;
- evidence passages;
- pending decisions;
- intermediate results.

It does **not** claim the same physical mechanism across those domains.

## Candidate experiments

### AIWS-001 — reversible offload vs lossy summary

Compare:

1. full context;
2. bounded context + exact external retrieval;
3. bounded context + summary + source pointer;
4. bounded context + summary only.

Measure:

- task success;
- contradiction rate;
- repeated work;
- source-recovery rate;
- token exposure;
- latency;
- authority-constraint retention.

### AIWS-002 — semantic hotness vs recency eviction

Compare recency-only eviction against explicit semantic classes.

Primary endpoint: task success at matched active-token budget.

Secondary endpoints:

- critical-constraint loss;
- unnecessary retrieval;
- total tokens;
- tool misuse.

### AIWS-003 — adaptive prefetch depth

Test prefetch depth (d in {0,1,2,4,...}) under fixed context pressure.

Measure hit rate, wasted prefetched bytes/tokens, latency, and active-footprint pressure.

### AIWS-004 — unified finite-working-set benchmark

Run matched tasks while independently varying:

- total universe size;
- resident subset size;
- selection quality;
- restore/retrieval fidelity;
- pressure threshold.

Apply the same accounting vocabulary to tool schemas and evidence passages, while keeping domain-specific mechanisms separate.

Primary endpoints:

- task success;
- active tokens;
- total tokens;
- retrieval/page-in count;
- stale or missing critical-state rate.

### AIWS-005 — usefulness selection vs similarity selection

Using a frozen corpus and fixed context budget, compare:

1. no filtering;
2. similarity-based top-k;
3. usefulness-scored top-k;
4. keyword/BM25 fallback.

Measure answer fidelity, source coverage, active tokens, selection latency, and repeated retrieval. This is motivated by GPT Researcher's public Jev evaluation design; it is not a claim that Jev is universally optimal.

## Relationship to current Finite RAM Lab

This intake does not alter the physical-RAM experimental program.

It adds a transfer hypothesis:

```text
finite physical residency research
        ->
general finite working-set abstraction
        ->
AI-worker experiments
```

Physical results must not be presented as direct evidence for AI-worker behavior.

## Claim ceiling

Allowed:

- primary sources demonstrate real systems using offload, summarization, deferred loading, staged active subsets, searchable capability catalogs, and bounded evidence selection;
- these systems motivate a cross-domain finite-working-set hypothesis;
- reversible retrieval and lossy compaction are experimentally separable.

Not allowed yet:

- "Finite RAM Lab has solved AI context management";
- "RAM pressure knees directly predict token-context knees";
- "human false-memory results prove LLM summary corruption";
- "one universal eviction policy is optimal across physical RAM, tools, and context."

## Intake decision

**ABSORB as a cross-domain research hypothesis.**

No standalone product extraction and no AI-worker runtime mutation follows from this note.
