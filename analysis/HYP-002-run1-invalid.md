# HYP-002 Run 1 — INVALID / Implementation Error

> **Run:** 36243199948  
> **Scientific status:** INVALID / NO EVIDENCE

## Symptom

All 16 runner-block jobs failed during the first trial.

The aggregate job was skipped.

No HYP-002 scientific inference is authorized from this run.

## Root cause

The workload captured its content-integrity baseline digest **before** the deliberate recency-preparation touches.

The experiment then intentionally modified page-marker bytes during:

```text
older region touch rounds
recent region touch rounds
```

The final digest was therefore compared against a pre-preparation state.

Every valid recency-preparation trial was guaranteed to appear corrupted.

This was a validation-order bug, not a kernel/runtime result.

## Fix

Move the content-integrity baseline to:

```text
after recency preparation
before burst / measured pressure phase
```

Patch commit:

```text
a27a6ec9707c053ae41f5fe410f4f92ea0f88fcc
```

## Research consequence

The frozen HYP-002 scientific design is unchanged.

No endpoint, factor, sample size, or inference rule was modified after seeing scientific data because no valid scientific dataset was produced.

The experiment may be relaunched from the same frozen contract.

## Authority boundary

Run 36243199948 is infrastructure/implementation audit history only.

It must never be pooled with a valid HYP-002 run.
