# B494 — GitHub Actions Governor Application Surface v0.1

Status: **APPLICATION-SURFACE QUALIFICATION**.

## 1. Goal

B493 qualified Governor v2.1 as a research policy.

B494 turns that policy into a reusable application contract.

Ordinary callers should not need to import:

- calibration experiments;
- research aggregation code;
- B489/B491/B492 internals.

They provide only:

- peak budget in bytes;
- minimum rank-coverage requirement.

They receive:

- selected q;
- calibrated empirical-max boundary;
- independent sample count;
- rank-coverage floor;
- implementation version;
- evidence receipt.

## 2. Frozen standalone policy

Application policy:

`policies/repaired-governor-v2.1.json`

The manifest contains the qualified v2.1 breakpoints and provenance needed for a
decision receipt.

It is intentionally separate from the research harness.

## 3. CLI surface

After installing the repository:

```bash
frl governor-select \
  --policy policies/repaired-governor-v2.1.json \
  --peak-budget-bytes 60000000 \
  --minimum-rank-coverage 0.95 \
  --out governor-receipt.json
```

Expected selection at 60,000,000 B:

`q4`.

## 4. Composite GitHub Action

Within GitHub Actions:

```yaml
- uses: hopeless-t/finite-ram-lab/.github/actions/finite-ram-governor@<ref>
  id: governor
  with:
    peak-budget-bytes: "60000000"
    minimum-rank-coverage: "0.95"
    receipt-path: "governor-receipt.json"

- run: echo "selected q = ${{ steps.governor.outputs.selected-q }}"
```

Outputs:

- `selected-q`
- `selected-empirical-max-peak-bytes`
- `sample-count`
- `rank-coverage-floor`
- `policy-version`
- `implementation`
- `receipt-path`

## 5. Receipt contract

Every successful decision writes:

`finite-ram-lab.governor-decision-receipt/v0.1`

The receipt includes:

- caller request;
- selected q;
- budget slack;
- selected empirical maximum;
- sample count;
- coverage floor;
- latency estimate;
- policy ID/version;
- canonical policy-manifest SHA256;
- source Governor SHA256;
- evidence sample unit;
- exchangeability assumption.

## 6. Fail-closed behavior

The application refuses to manufacture a decision when evidence does not support
one.

Examples:

- 50,696,191 B at 95% -> no eligible repaired q;
- any budget at 99% -> no eligible repaired q with the current n=27 state.

The application does not silently reduce requested coverage.

## 7. Why this is the local-development bridge

The application contract is deliberately independent of GitHub-hosted execution.

GitHub Actions is the first adapter.

A later LDC/local adapter can call the same selector and receipt schema against a
local-machine policy manifest.

That permits:

```text
same Governor application contract
+
environment-specific calibration
```

rather than copying GitHub-hosted numerical thresholds onto the development PC.

## 8. Claim ceiling

**REPAIRED_GOVERNOR_APPLICATION_SURFACE**

This surface exposes an evidence-qualified decision. It does not convert the
exchangeability-conditional empirical boundary into a hard RAM guarantee.

## 9. Next

If B494 passes, B495 should dogfood the action from an ordinary workflow job and
record the first application-level receipt/consumer handoff.

Then a local/LDC adapter can be implemented with the same input/output contract.
