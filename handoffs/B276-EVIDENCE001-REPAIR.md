# Bounce Handoff

> **Bounce ID:** B276
> **Status:** EVIDENCE-001 WORKFLOW REPAIRED / CI PENDING

Failed hosted run:

`36446699329`

Exposed invariant:

`ModuleNotFoundError: No module named 'finite_ram_lab'`

Repair:

- add package install before corpus build:
  `python -m pip install -e ".[analysis]"`

No scientific evidence changed.
No corpus result is accepted from the failed run.
No blind rerun was issued.

Next: read ordinary CI for this repair commit exactly once. Success permits a new explicit EVIDENCE-001 launch generation.

Hosted research only.
