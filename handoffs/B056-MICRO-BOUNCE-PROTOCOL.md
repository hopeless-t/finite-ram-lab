# Bounce Handoff

> **Bounce ID:** B056
> **Status:** COMPLETE / OPERATING PROTOCOL UPDATED

## Objective

Reduce lost work caused by chat/tool timeouts by shortening the durable unit of work.

## Change

`docs/MULTI_BOUNCE_PROTOCOL.md` now requires:

- micro-bounces;
- commit-before-wait;
- early checkpoints;
- one durable transition per bounce by default;
- uncommitted work to be treated as non-canonical.

## Next recommended bounce

Inventory and freeze the GitHub Actions Node24+ maintenance migration before changing workflows.

## Authority boundary

This is an operating-protocol change only. No scientific result changed.
