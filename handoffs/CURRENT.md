# CURRENT

> Latest bounce: B388
> Stage: EXTERNAL MEMORY-SYSTEMS RECONNAISSANCE COMPLETE
> Stop: RESEARCH PAUSE / RARE-SPECIMEN MODEL REVIEW

## Physical research

No new physical run after B387.

Controlled-spawn result remains canonical:
- frozen primary: 49/72
- direct-primer terminal phase: 55/55
- b63 direct-primer phase: 14/14
- measured VmPTE growth: 0/4164
- negative -17 accounting signature unresolved

## External reconnaissance

Doc:
`docs/EXT-2026-09-30-MEMORY-SYSTEMS-RECON.md`

### Linux stock architecture

Current upstream at reconnaissance cut:
- `NR_MEMCG_STOCK = 7`
- `MEMCG_CHARGE_BATCH = 64`
- existing per-CPU shared memcg stock

Active v5 proposal:
`memcg -> page_counter_stock`

If merged, it changes:
- ownership topology
- cross-memcg victim eviction
- drain behavior
- precharged-memory scaling

Future Q64 comparisons must record stock architecture, not kernel version alone.

### External AI-memory convergence

Reviewed:
- mzCache
- vLLM tiered KV
- TierKV
- KV Cache memory-wall survey
- SSD-LLaMA
- cache-aware MoE router adaptation
- Strata (B387)

Shared pattern:

`classify state -> estimate future demand / transfer / restore cost -> control residency transition`

## Authority

PAUSE.

No new physical experiment.
Codex rare-specimen census / mathematical generative-model work may continue from existing evidence.
