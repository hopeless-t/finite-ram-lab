# B421 — consume_stock return observer: LDC host-action boundary

Date: 2026-09-30
Repository baseline: `a6434626c087a0819bef5c33596e9803c8d166f7`

## Goal

Launch the smallest physical capability pilot for the already-frozen
`TX-CONSUME-STOCK-RET-PILOT-v1` observer and answer only:

> Can the observer directly capture a successful `consume_stock()` return
> for the verified target memcg during one known stock-backed target touch?

This bounce does not claim the Same-CPU R2 block2 anomaly was caused by
`consume_stock()`.

## Frozen experiment state

Already present on the baseline commit:

- `specs/TX-CONSUME-STOCK-RET-PILOT-v1.json`
- `src/finite_ram_lab/consume_stock_ret_pilot.py`
- consume_stock return parser/tests in `transaction_trace_observer.py`
- `.github/workflows/consume-stock-ret-pilot.yml`
- CI PASS before this bounce

Physical pilot launch has not occurred.

## LDC live observation

The Local MCP Gateway candidate lane is live and usable:

- lane: `research`
- status: `READY`
- mode: `INTERVENE`
- `BOUNDED_PROCESS`: granted
- network: false
- canonical write: false
- promotion: false
- Remote Desktop Commander: false

The current composite gateway accepts:

```text
candidate.run {
  lane_id,
  template_id
}
```

The only activated process templates are:

- `candidate_selftest`
- `python_unittest`
- `pytest`

The candidate capsule bind-mounts the isolated candidate workspace but does
not expose host `/sys/kernel/tracing`. Therefore the physical tracefs/kprobe
pilot cannot be executed through the current generic candidate template
surface.

This is a tool-surface capability gap, not an experiment failure.

The legacy read path returning `operator_binding_missing` is a separate
condition and does not negate the READY candidate lane.

## Pseudo-council

### A — trigger the existing GitHub-hosted workflow

Rejected for this bounce.

Reason:

- the user requested LDC-local execution;
- paid runner authority remains false;
- creating `launch/TX-CONSUME-STOCK-RET-PILOT-v1.txt` would trigger the
  hosted workflow and violate the intended resource boundary.

### B — force the pilot through `pytest` inside the candidate capsule

Rejected.

Reason:

- `/sys/kernel/tracing` is absent from the capsule;
- a resulting failure would confound observer correctness with sandbox
  visibility/privilege;
- it would not be a valid physical observer capability test.

### C — add one frozen LDC host action

Selected.

Required action identity:

```text
finite_ram.consume_stock_ret_observer_pilot_v1
```

## Frozen host-action contract

The action must be fixed server-side. MCP/model input must not supply raw
commands, paths, block counts, probe definitions, or privilege options.

### Execution scope

- local machine only
- repository: `/home/tonegawa/work/finite-ram-lab`
- exactly one identity: block `0`
- no automatic retry
- no automatic sample expansion
- no network
- no paid resources
- no Remote Desktop Commander
- no canonical MVCA write/promotion

### Source identity

Before any trace mutation, verify the exact experiment inputs are regular,
non-symlink files and pin their SHA-256 identities at action construction.

At minimum pin:

- `specs/TX-CONSUME-STOCK-RET-PILOT-v1.json`
- `src/finite_ram_lab/consume_stock_ret_pilot.py`
- `src/finite_ram_lab/transaction_trace_observer.py`
- `experiments/tx_perturbation_worker.c`

A documentation-only repository HEAD advance does not authorize changed
experiment bytes.

### Environment preflight

Fail closed before probe creation unless all hold:

- page size = 4096
- cgroup v2
- at least 3 schedulable CPUs
- tracefs is mounted or can be mounted by the fixed runner
- `consume_stock`, `refill_stock`, `page_counter_uncharge`, and
  `page_counter_try_charge` are probeable
- required noninteractive privilege is available
- output directory is inside the finite-ram-lab evidence root

Privilege unavailability is a HOLD/NOT_DISPATCHED condition, not a scientific
negative result.

### Probe set

Use the already-frozen semantics:

- `frl_refill_stock`
- `frl_pc_uncharge_owner`
- `frl_pc_try64`
- `frl_consume_stock_ret` as kretprobe

After VERIFY, bind the consume observer to:

```text
memcg == owner_memcg && ret != 0
```

### Physical action

For block 0 only:

1. create a fresh verified b63-capable target;
2. resolve `owner_memcg`;
3. arm the consume return observer;
4. snapshot kprobe profile counts;
5. perform exactly one measured stock-backed target consume touch;
6. close the observation window;
7. snapshot kprobe profile counts;
8. freeze raw trace, profile, environment, trial JSON, and block summary;
9. cleanup probes regardless of outcome.

### Capability PASS specimen

A promoted capability specimen requires:

- VERIFIED target state
- complete observation window
- worker_error = 0
- target remains on stock CPU
- VmPTE delta = 0
- consume kretprobe missed delta = 0
- at least one target-lane event with:
  - owner memcg match
  - `nr_pages = 1`
  - `ret != 0`
  - target comm
  - target pid
  - stock CPU

Expected classification:

```text
CONSUME_STOCK_RET_CAPTURED
```

### Other outcomes

- preverify failure -> `PREVERIFY_HOLD`
- incomplete/cpu/pte/worker observation -> `OBSERVATION_HOLD`
- consume kretprobe misses -> `INSTRUMENTATION_HOLD`
- valid zero-capture window -> `CAPABILITY_NOT_OBSERVED`

A zero-capture window is not proof that `consume_stock()` is irrelevant.

## Current disposition

```text
experiment code ready          PASS
parser/tests                   PASS
candidate LDC lane             READY
host tracefs access            NOT EXPOSED
physical pilot dispatch        NOT DISPATCHED
scientific result              NONE
```

## Next atomic bounce

Implement and qualify the frozen action
`finite_ram.consume_stock_ret_observer_pilot_v1` in the Local MCP Gateway,
then launch exactly one block-0 identity.

Only if that one specimen is complete should the observer capability pilot
expand to the original four identities.
