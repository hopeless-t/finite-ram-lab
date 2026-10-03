# FR-META-007 Receipt

Status: **PASS / SPECULATIVE BUILD-AHEAD PROTOCOL v0.3 QUALIFIED**

- workflow run: 37137083534
- job: 111243689153
- execution head: cabe680900e564029cdea84726a2a0f0c9a05ff4
- qualification artifact ID: 11278734773
- artifact ZIP SHA256: c634b9648da72da0965c87c7994dc2197dbf68292fb787cb6edfe27179b9bbb7

Final protocol:

1. build at most one successor as unreferenced Git objects while parent CI runs;
2. treat that detached commit as a prepared delta, not the final child;
3. wait until the parent qualification receipt is frozen;
4. reapply the prepared delta on the parent receipt tree;
5. create a new final child commit whose parent is the receipt commit;
6. only then publish the child branch.

Dogfood corrections preserved:

- v0.1 incorrectly published after PASS before parent receipt;
- v0.2 waited for receipt but still proposed direct publication of the old detached SHA;
- v0.3 requires materialization on the frozen receipt tree.

Hard boundary:

- speculative depth = 1;
- FAIL / UNKNOWN / IN_PROGRESS / PASS-without-receipt grants no child publication;
- no workflow or authority is created by the detached prepared delta.

Claim ceiling:

**SPECULATIVE_DETACHED_BUILD_PROTOCOL_ONLY**
