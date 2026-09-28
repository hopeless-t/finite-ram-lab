# Recorder Research-Ready Policy

> **Status:** ACTIVE
> **Decision:** RETURN TO RESEARCH MAINLINE

REC-001/REC-003 has crossed the current minimum reliability boundary for experimental use:

- malformed evidence fails visibly;
- stream lifecycle corruption fails closed;
- incomplete clean runs remain explicitly incomplete;
- raw evidence remains canonical;
- SQLite remains rebuildable;
- duplicate conflicts are explicit;
- raw evidence path ownership is exclusive;
- deterministic corruption tests and Monte Carlo attack machinery exist.

This does **not** mean the Recorder is complete or universally robust.

The operating policy is now:

1. run the research experiments;
2. keep Recorder in the evidence path only after REC-002 observer-effect screening;
3. when a real run exposes a Recorder defect, classify it explicitly;
4. preserve unaffected raw evidence;
5. repair with the smallest justified change;
6. promote the counterexample to a deterministic regression;
7. rerun the relevant bounded validation, not the entire world by default.

REC-003 remains available as a hardening sidecar. Large Monte Carlo campaigns are reserved for meaningful Recorder changes, discovered counterexamples, or scheduled robustness review.

The research mainline is no longer blocked on making Recorder impossible to break.
