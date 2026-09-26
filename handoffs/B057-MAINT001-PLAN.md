# Bounce Handoff

> **Bounce ID:** B057
> **Status:** COMPLETE / MAINTENANCE PLAN FROZEN

## Objective

Inventory Node20-targeting GitHub Action references and freeze a low-risk Node24+ migration plan.

## Result

Inventory:

- checkout@v4: 30 workflows
- setup-python@v5: 30 workflows
- upload-artifact@v4: 29 workflows
- download-artifact@v4: 17 workflows

Frozen targets:

- checkout@v7
- setup-python@v7
- upload-artifact@v7
- download-artifact@v8

## Rollout

First update only ci.yml as a canary.

Do not bulk migrate until that canary passes and the Node20 warning is gone.

## Next recommended bounce

Update ci.yml only, commit, write B058, then let its CI run.

## Authority boundary

Maintenance only. No scientific state changes.
