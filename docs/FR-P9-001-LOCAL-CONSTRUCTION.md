# FR-P9-001 construction note

The implementation is deterministic and standard-library only.

Expected construction properties before hosted CI qualification:

- three work units compile different runtime projections;
- the multi-plane compiled projection preserves the full declared contract;
- decision-only slicing is intentionally insufficient;
- every compiled atom has a removal witness on at least one contract plane;
- unknown atoms and dependency cycles fail closed.

Hosted CI remains the qualification source for the published branch. This note is not a PASS receipt.
