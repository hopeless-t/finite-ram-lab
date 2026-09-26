# Bounce Handoff

> **Bounce ID:** B064
> **Status:** COMPLETE / ROUNDTRIP RETRY LAUNCHED

## Objective

Fix only the checksum-path bug from B063.

## Change

Checksum metadata is now generated from inside `maint-artifact/`, so the stored filename is simply `payload.txt`.

## Next recommended bounce

Read the maintenance roundtrip run triggered by this commit and classify PASS/FAIL.
