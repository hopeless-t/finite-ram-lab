# AI Context Working-Set Cross-Pollination (2026-10-05)

Source: https://zenn.dev/mizchi/articles/ai-coding-loop-formal

## Research connection

Formal AI coding loops expose a memory-management analogue: large repository/task context does not need to live in the model context window at once. Treat the full world state as backing storage and the prompt/context window as a bounded working set.

```text
repository / logs / specs / tests / history / artifacts
                         |
                         v
                  backing state
                         |
                  query projection
                         |
                         v
                  working context
                         |
                         v
                        LLM
```

This mirrors Finite RAM Lab's core question:

> When capacity is finite, what should remain resident, what should be reclaimed, and when?

## Proposed AI-context analogy

| Finite-memory systems | AI context system |
|---|---|
| physical RAM | context/token budget |
| backing store | repository / artifact store |
| page-in | retrieve relevant evidence |
| reclaim | evict stale context |
| refault | retrieve recently evicted context again |
| working set | active task context |
| dirty page | unsaved/unevaluated reasoning artifact |
| prefetch | anticipatory retrieval |
| pressure | token/tool/time budget pressure |

The analogy is not assumed to be exact; it is a source of falsifiable experiments.

## Candidate research question

Can an AI worker maintain equal or better task success with a smaller resident context by using explicit working-set management?

Define:

```text
C_total   = total available external state
C_res     = tokens resident in model context
R         = retrieval operations
F         = context refaults
S         = task success / verifier score
L         = latency
```

Study the tradeoff:

```text
minimize C_res + retrieval_cost + refault_cost
subject to verifier_score >= baseline
```

## Candidate metrics

- peak resident tokens
- cumulative tokens processed
- retrieval count
- repeated retrieval / refault rate
- stale-context rate
- evidence recall
- task verifier score
- latency
- tool calls
- context churn

## Experimental lanes

### CTX-001 — full-context baseline

Load the largest feasible repository/task context and record cost/success.

### CTX-002 — demand paging

Start with only goal + index/metadata, then retrieve exact evidence on demand.

### CTX-003 — predictive prefetch

Use the task graph to prefetch likely-needed files/evidence and compare against CTX-002.

### CTX-004 — reclaim policy

Compare eviction policies:

```text
LRU-like
semantic relevance
rebuild cost
future-use prediction
pinned invariants
```

### CTX-005 — refault characterization

Measure when an evicted context item is retrieved again and distinguish:

```text
good reclaim
premature reclaim
unnecessary prefetch
policy oscillation
```

## Important methodological guard

Do not assume fewer tokens is automatically better, just as free RAM is not itself the systems objective. The target is useful work under finite capacity.

A successful run is also not automatically a successful context policy. Evidence should separate:

```text
task success
cost
latency
retrieval churn
robustness
```

## Why this is worth testing

This creates a bridge between OS-style working-set research and AI-agent context orchestration. If the analogy survives measurement, Finite RAM Lab can contribute mechanisms for bounded AI memory without treating the context window as the canonical memory store.
