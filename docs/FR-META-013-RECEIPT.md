# FR-META-013 Receipt

Status: **PASS / NEGATIVE DOGFOOD RESULT / CACHE NOT PROMOTED**

Final v0.2 qualification:

- workflow run: 37139290635
- job: 111250204243
- execution head: e5883aeab07b459cb1e1dc812a51280e3cd424d8
- qualification artifact ID: 11280001698
- artifact ZIP SHA256: a2ada265af60949aabf6056aa516d4e7c6bbf2a044f301e247d8f42351f4bc6c

Dogfood observations:

Implementation run:
- setup-python pip cache lookup: MISS
- Install span: about 20.19 s
- cache key saved successfully after the run

PR follow-up:
- same dependency key
- setup-python again reported: pip cache is not found
- Install span: about 19.04 s
- full CI: PASS

The receipt-push CI was correctly cancelled by FR-META-009 concurrency, so the
surviving PR run is the relevant follow-up specimen.

Theory update:

- cache configuration is not cache reuse evidence;
- producer -> consumer ref/scope topology must be proven;
- save/restore overhead must be counted;
- the current stacked-branch / PR flow did not demonstrate material reuse.

Repository action:

- setup-python pip cache configuration removed in v0.2;
- no cache speed primitive promoted.

Decision:

**DO_NOT_PROMOTE_PIP_CACHE_FOR_CURRENT_STACKED_PR_FLOW**

Compiled negative skill candidate:

**CACHE_REUSE_REQUIRES_PROVEN_PRODUCER_CONSUMER_SCOPE**

Claim ceiling:

**NEGATIVE_CI_DEPENDENCY_CACHE_RESULT_ONLY**
