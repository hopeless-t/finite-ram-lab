# B388 — External memory-systems reconnaissance

## Status

EXTERNAL RECONNAISSANCE COMPLETE.

No physical experiment launched.
Research pause remains in force.

## Highest-value new finding

Linux memcg stock itself is under active redesign.

v5 series:
`move stock from mem_cgroup to page_counter`

Current upstream at this cut still uses:
- `NR_MEMCG_STOCK = 7`
- `MEMCG_CHARGE_BATCH = 64`
- shared per-CPU memcg stock

Proposed design:
- per-page_counter per-CPU stock
- removes seven-memcg shared-slot victim topology
- changes drain/refill ownership and interference

This creates a future kernel-generation boundary for Q64 research.

## AI-memory convergence

Newly reviewed:

- mzCache
- vLLM tiered KV offloading
- TierKV
- The KV Cache Is the New Memory Wall
- SSD-LLaMA
- Cache-Aware Joint Router Adaptation

Common pattern:

`state classification -> predicted use/restore/transfer cost -> controlled tier transition`

This independently aligns with finite-ram-lab's move from capacity observation to state-transition control.

## Stored

`docs/EXT-2026-09-30-MEMORY-SYSTEMS-RECON.md`

## Pause

No new physical run from B388.

Next action remains:
Human/Codex review of rare-specimen census and generative model.
