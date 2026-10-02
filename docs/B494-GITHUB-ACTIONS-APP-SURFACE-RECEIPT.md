# B494 — GitHub Actions Governor Application Surface Receipt

Status: **PASS / APPLICATION SURFACE QUALIFIED**

## Frozen execution

- workflow run: 36965047048
- job: 110706855653
- execution head: a8fc644cc53b9a9a77889efcca66bdf670a878d0
- tests: 4/4 PASS
- artifact ID: 11209625678
- artifact ZIP SHA256: f7cf90ea29cd2c1c8879511cb2d62138d6caa922ea34c711be1ea4250e670e5d

## Standalone policy

Policy file:

`policies/repaired-governor-v2.1.json`

File SHA256:

`6c85f45d814a2c7f4c1b54d34410676ee7bc3479a760a3ddf70d4ab8013b7e9a`

Canonical JSON SHA256 carried inside decision receipts:

`4b84f3c99d347b75e2a5deff527626784c71728474de72ba7e6bf7f9dbf23e8a`

## Qualified interfaces

### CLI

```text
frl governor-select
  --policy <policy>
  --peak-budget-bytes <bytes>
  --minimum-rank-coverage <coverage>
  --out <receipt>
```

### Composite Action

```text
.github/actions/finite-ram-governor/action.yml
```

The action exposes:

- selected-q
- selected-empirical-max-peak-bytes
- sample-count
- rank-coverage-floor
- policy-version
- implementation
- receipt-path

## Qualification decision

Input:

- peak budget = 58,941,440 B
- minimum coverage = 0.95

Output:

- q = 4
- n = 27
- rank floor = 27/28 ~=96.4286%
- implementation = TILED_WHERE

Action decision receipt SHA256:

`31bbbefac4e17e6b1888a6d302bd1f0e9390232869cbf1efec9f310f350e2a87`

CLI receipt SHA256:

`701a48b86929d3102eeb4c2aca47a8ac69a7a903e1ecf94ee6c01f242454c3b0`

## Dependency-boundary correction

The first B494 application run failed before decision execution because the
existing `frl` CLI imported the analysis calculator stack at process startup,
which required NumPy even for the dependency-free Governor selector.

B494 corrected this by lazy-importing calculator dependencies only inside the
calculator subcommands.

The successful qualification therefore proves:

```text
pip install -e .
+
frl governor-select
```

works without installing the optional analysis stack.

This materially reduces application-surface friction.

## Fail-closed behavior

Unsupported budgets or coverage requests do not receive a fabricated q.

The selector does not reduce requested coverage silently.

## Claim ceiling

**REPAIRED_GOVERNOR_APPLICATION_SURFACE**

## Next

B495 should use the Composite Action from an ordinary consumer workflow, pass its
selected q into a physical repaired-runtime execution, and freeze one
application-level decision/execution receipt.

That closes the first consumer loop:

```text
application request
-> Governor Action
-> q output
-> application execution
-> physical observation
-> receipt
```
