# Bounce Handoff

> **Bounce ID:** B165
> **Status:** COMPLETE / STRATA-001 PILOT PRE-LAUNCH WORKFLOW FIX

## Finding

A pre-launch readback found that the cold-file preparation heredoc used:

`Path("$RUNNER_TEMP")`

inside a single-quoted Python heredoc.

That would create/use a literal path named `$RUNNER_TEMP` relative to the checkout, while the trial step later reads from the real shell-expanded `$RUNNER_TEMP`.

The pilot would therefore fail before producing valid evidence.

## Fix

Use:

`Path(os.environ["RUNNER_TEMP"])`

inside the preparation Python.

No pilot science, size, arm, pressure level, schedule, or inference contract changed.

## Decision

Do not launch the pilot from the known-bad workflow.

Validate this pre-launch fix first.

## Next action

Read ordinary CI for B165 exactly once.

- SUCCESS → add the self-file-only push trigger and launch exactly one pilot.
- pending → checkpoint EXTERNAL_WAIT.
- FAIL → inspect failure only.

## Authority boundary

Pilot only.
