# Bounce Handoff

> **Bounce ID:** B058
> **Status:** COMPLETE / CANARY LAUNCHED BY COMMIT

## Objective

Change only the core CI workflow to Node24-compatible action majors.

## Change

`.github/workflows/ci.yml`:

- `actions/checkout@v4 -> @v7`
- `actions/setup-python@v5 -> @v7`

No scientific workflow or experiment spec changed.

## Acceptance

The CI triggered by this commit must:

- complete successfully;
- retain all existing Python validation steps;
- no longer emit the Node.js 20 forced-upgrade warning for checkout/setup-python.

## Next recommended bounce

Read the canary CI result and logs only. If PASS and warning-free, record B059 and authorize small-batch workflow migration.

## Authority boundary

Maintenance canary only.
