# B501 — Local Execution Admission Contract v0.1

Status: **ADMISSION CONTRACT QUALIFIED / LOCAL EXECUTION NOT YET PERFORMED**

## 1. Goal

B500 made the complete local Governor qualification executable as one command.

B501 freezes the exact bounded action that may later be admitted through:

```text
Web ChatGPT -> MVCA -> LDC -> development machine
```

The purpose is to remove ambiguity from the eventual local execution request.

## 2. Action

Action ID:

`finite_ram.local_qualify_v1`

The admitted action performs one host-local B500 qualification:

```bash
python -m finite_ram_lab.local_one_shot_qualifier \
  --exploration-samples-per-q 8 \
  --size 2048 \
  --target-rank-coverage 0.95 \
  --max-extension-cycles 4 \
  --out-dir runs/local-governor/<run_id>
```

## 3. Bounded resource envelope

Candidate q:

`{1,2,4,7}`

Initial exploration:

- 8 fresh processes per q
- 32 observations

95% rank-max target:

- n=19 per final Pareto q

Worst case:

- all four q remain Pareto
- 76 total physical observations

The one-shot qualifier may use fewer observations when the local Pareto is smaller.

## 4. Effect boundary

This action is a local measurement/calibration action.

Frozen properties:

- network access required: **false**
- external effects allowed: **false**
- authority effect: **NONE**
- clean repository checkout required
- exact repository commit must be recorded
- output is isolated under one run-specific directory

No OpenPencil or unrelated execution authority may be reused for this action.

## 5. Retry boundary

If LDC delivery/execution state is ambiguous:

`DO_NOT_RETRY`

Reason:

A blind duplicate run would add an untracked sample population and may invalidate the evidence ledger.

Any new execution must use a new admitted `run_id`.

This applies the same research rule used elsewhere in MVCA:

`UNKNOWN != permission to retry`.

## 6. Output bundle

Required files:

- `local-exploration.json`
- `local-calibration-state.json`
- `local-governor-policy.json`
- `local-qualification-receipt.json`
- `bundle-manifest.json`

The manifest must contain digests for the generated bundle.

## 7. Admission request

B501 provides:

`finite_ram_lab.local_execution_admission`

Example:

```bash
python -m finite_ram_lab.local_execution_admission \
  --spec specs/B501-LOCAL-EXECUTION-ADMISSION-v0.1.json \
  --run-id b501-local-001 \
  --repo-commit <40-hex-commit> \
  --out admission-request.json
```

The request records:

- action ID;
- run ID;
- exact repository commit;
- canonical admission-spec SHA256;
- argv;
- output directory;
- maximum observation count;
- retry policy;
- required outputs;
- preconditions/postconditions.

## 8. Current execution state

At the latest preflight before B501:

- MVCA status: CURRENT
- working tree: clean
- LDC config: UNKNOWN
- reason: `operator_binding_missing`
- authority grant: NONE

Therefore B501 qualifies the request contract only.

It does not claim a development-machine calibration.

## 9. Claim ceiling

**LOCAL_EXECUTION_ADMISSION_CONTRACT_ONLY**

## 10. Next

Once an appropriate MVCA/LDC operator binding exists:

1. create one admission request with a fresh run ID;
2. admit exactly `finite_ram.local_qualify_v1`;
3. execute once;
4. return the bundle manifest and files;
5. freeze the first real development-machine calibration receipt;
6. do not retry an ambiguous run under the same run ID.
