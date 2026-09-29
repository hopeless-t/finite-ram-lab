# RETROSPECTIVE — Q64 / LRU evidence audit

> Date: 2026-09-30
> Status: retrospective audit / no new physical run

## Executive conclusion

Evidence separates into three compatible layers:

1. Natural incidence: rare LOW exact-zero incidence is associated with the CAP10+ region in G-F/G0, but the physical cause is not identified.
2. Controlled transition: after a directly observed Q64 primer and PTE preconditioning, b62/b63/b64 terminal phase follows one-page stock arithmetic.
3. Observation emission: recurrent -17 memory.current is dominated by deferred shared per-CPU LRU/folio-batch release, not residual-stock consumption.

These layers must not be collapsed into one causal story.

## Natural incidence

- G-F low CAP8+9: 14/452 exact-zero.
- G-F CAP10+11+12+32: 77/922.
- G0 CAP8/9: 5/334.
- G0 CAP10/32: 14/162.
- Combined block-conditioned CMH common OR about 3.22.
- G0 breaks argv-width confounding: canonical 8/9 vs padded 08/09 p=0.666.
- Padded 08/09 vs 10/32 remains strongly different, p=0.00128.
- CAP10+ step is the best tested block-held-out predictor.

Do not infer a universal causal threshold at 10. H10 vs H32 is itself non-monotone and remains exploratory.

## Depth phenotype

- G-A: 22/28 depth1 plus a deeper tail.
- G0: 12/19 adjacent-touch depth1 candidates; seven remain at least depth2.
- Spike-plus-tail describes the phenotype better than one geometric law.

This does not identify the natural residual-stock distribution.

## PTE

- G0 first-fault VmPTE growth occurs only in H32: 8/160 vs 0/800 elsewhere.
- LOW PTE-growth trials are 5/5 Q64, but one HIGH PTE-growth trial is exact-zero.
- Therefore PTE charge is a real possible pre-data perturbation, not a deterministic veto.
- Controlled-spawn preconditioning reduced measured VmPTE growth to 0/4164 touches.

## Controlled Q64 transition

- Frozen strict endpoint: 49/72.
- Direct Q64 primer: 55/72.
- Primer-qualified terminal pattern: 55/55.
- b62 23/23, b63 14/14, b64 18/18.

Mechanism support is strong. Reliability certification is not complete. Frozen 49/72 must not be rewritten.

## Recurrent -17 forensic result

OBS-001: exact -17 is page_counter_uncharge(17) on the LRU/folio-batch path; stock drain is not required.

OBS-002: 9/11 exact -17 specimens directly show touch -> LRU flush31 -> folios_put31 -> uncharge17. Inferred initial occupancy 17/18 gives 9/9 first-flush -17 versus 0/17 for other observed occupancies.

OBS-004: nine worker-triggered and three same-counter cross-task LRU cases; no direct recurrent -17 stock-drain class.

OBS-005 controlled construction:
- scrub precondition success 15/16;
- producer A memory.current exact -17 during trigger phase 15/15;
- producer counter receipt retained 12/15;
- producer page-counter uncharge17 12/12;
- canonical producer17 + trigger14 = batch31 occurs 10 times;
- one B-touch13 case is compatible with one external insertion;
- one third-party provjobd trigger demonstrates owner/trigger separation.

Therefore the dominant recurrent -17 mechanism is strongly established as deferred owner folios in a shared per-CPU LRU-add batch, released when any task on that CPU triggers the flush.

## Observer meaning

memory.current is a net accounting emission, not a hidden-state register.

A measured interval can combine:
- charge / stock refill;
- stock consumption with zero visible delta;
- PTE charge;
- LRU deferred release;
- stock drain;
- other asynchronous accounting.

## What is still open

- physical cause of CAP10+ natural incidence;
- exact natural starting residual-state distribution;
- transport of pre_current association;
- PTE contribution magnitude;
- rarer negative deltas such as -13, -3, -2;
- raw-start b63 reliability;
- cross-kernel and cross-hardware transport.

## Rejected interpretations

- argv decimal width as the required capacity explanation;
- universal monotone capacity law;
- deterministic PTE-growth veto;
- memory.current as a direct residual-stock read;
- every negative delta as stock consumption;
- recurrent -17 as primarily prep-CPU stock drain;
- pooling natural incidence and primer-conditioned transition into one Bernoulli population;
- rewriting frozen 49/72 after observing conditional 55/55.

## Evidence-integrity audit

Strengths:
- frozen endpoints preserved;
- instrumentation mistakes documented instead of silently reused;
- no adaptive replacement in key controlled experiments;
- raw manifests verified;
- Drive COLD copies restored and byte-verified.

Important caveat:
the old OBS-002 tracefs capability document is a historical failed attempt. Later corrected capability gates succeeded and OBS-001..005 used tracefs/kprobes successfully.

## Decision after audit

Do not continue -17 caller hunting.
Do not immediately scale b63 reliability.

Next research step:
OBS-006 decontaminated charge-side Q64 observer.

Goal:
identify actual charge/refill events even when net memory.current is masked by unrelated release emissions.

Only after OBS-006 is validated should raw-start reliability scaling resume.