# FR-SOOM-001 — Semantic OOM Qualification Receipt

Status: **PASS / SYNTHETIC USER-TASK SURVIVAL COUNTEREXAMPLE VALIDATED**

## Frozen qualification

- workflow run: 37006366999
- job: 110835485639
- execution head: 2ba7de5200a11a4bd50b620ea942071226aa2ce8
- targeted tests: 7/7 PASS
- artifact ID: 11225229094
- artifact ZIP SHA256: 8b65a08f6d592e25a7b78c528334029f7384cfd71142de21752d340c7f9e5ee4
- spec SHA256: bb7c5367399ebb83d436b733c71972f50c3b4d1b0bfedd5b6aa42ef299f8d457
- result SHA256: ac6ca95feac54e86763b93cc1d62b8f7499e18ffed9c755cd2ba308da43fbab5

## Primary result

Every frozen policy satisfied the same requested memory-relief target.

The difference was **which semantic state was destroyed to obtain that relief**.

| required relief | oom-score-like victims | semantic victims | baseline semantic loss | semantic loss | current task survives semantic policy |
|---:|---|---|---:|---:|---|
| 1024 MiB | chrome-active | batch-compressor | 280 | 13 | yes |
| 2048 MiB | chrome-active | batch-compressor + background-indexer | 280 | 18 | yes |
| 3072 MiB | chrome-active | model-worker + batch-compressor + background-indexer | 280 | 73 | yes |
| 4096 MiB | chrome-active + model-worker | chrome-active + background-indexer | 335 | 285 | no |
| 5120 MiB | chrome-active + model-worker + batch-compressor | chrome-active + batch-compressor + background-indexer | 348 | 298 | no |

Semantic-loss improvement relative to the frozen oom-score baseline:

- 1024 MiB: 267 points
- 2048 MiB: 262 points
- 3072 MiB: 207 points
- 4096 MiB: 50 points
- 5120 MiB: 50 points

## The important boundary

The semantic policy preserves the frozen current task at:

- 1024 MiB;
- 2048 MiB;
- 3072 MiB.

It cannot preserve the current task at:

- 4096 MiB;
- 5120 MiB.

This is intentional.

The synthetic policy does not manufacture RAM and does not make active work
invincible. It changes the sacrifice order while sufficient lower-value
resident state exists.

Therefore the useful hypothesis is not:

`never kill Chrome`.

It is:

`do not destroy high-value current-task state while lower-cost relief remains available`.

## Why the baseline counterexample matters

At 1024 MiB required relief, the oom-score-like baseline kills active Chrome and
frees 3200 MiB.

The semantic policy kills the low-value batch compressor and frees 1400 MiB.

Both satisfy the pressure target.

The baseline provides more excess relief, but at much larger frozen semantic
loss.

This creates the exact research question needed for a future live controller:

> How much extra emergency headroom is worth how much user-task destruction?

The answer cannot be obtained from freed bytes alone.

## Relation to earlyoom

The EARLYOOM_LIKE_OOM_SCORE arm is deliberately narrow.

It models only a static highest-`oom_score` victim ordering. It does not model:

- the user's actual thresholds;
- live process evolution;
- SIGTERM grace;
- process exit timing;
- repeated pressure rechecks;
- prefer/avoid/ignore configuration;
- process groups;
- browser child-process structure.

Therefore this receipt is a synthetic counterexample to memory-only victim
ranking, not an empirical benchmark result for earlyoom itself.

## Relation to nohang

nohang provides richer pressure and victim-control inputs, including PSI and
badness adjustments.

That makes it a valuable future baseline.

The remaining semantic gap is still the same:

`process badness != current user-task value`

unless task value is explicitly represented.

## Replacement implication

FR-SOOM-001 is enough to justify **investigating** an earlyoom replacement.

It is not enough to justify deploying one.

The next safe evidence step is read-only shadow mode:

```text
live pressure + live /proc snapshot
             |
             +-> earlyoom-like ranking
             +-> nohang-like ranking
             +-> semantic ranking
                         |
                         v
                   comparison receipt
                   NO SIGNAL / NO KILL
```

Only repeated real-host disagreements with acceptable predicted pressure relief
would justify a bounded intervention experiment.

## Claim ceiling

**SYNTHETIC_VICTIM_SELECTION_COUNTEREXAMPLE_ONLY**

## Next

FR-SOOM-002 — observation-only shadow controller and receipt schema.
