# FR-GFX-006 — Read-only Collector Harness

Status: **RUNNABLE READ-ONLY HARNESS**

Parent: **FR-GFX-005**

## Purpose

FR-GFX-006 turns the observation contract into a small executable collector.

It deliberately does **not** launch MangoHud, intel_gpu_top, DXVK tools, or any
game process.

It reads only:

- `/proc/meminfo`;
- `/proc/pressure/memory`;
- `/proc/<pid>/smaps_rollup`;
- its own `/proc/<pid>/status`.

This creates the lowest-risk core collector before graphics-specific adapters
are added.

## Usage

Example:

```bash
python -m finite_ram_lab.fr_gfx_readonly_collector \
  --pid 12345 \
  --samples 120 \
  --interval-ms 500 \
  --output trace.jsonl \
  --receipt collector-receipt.json
```

For self-test:

```bash
python -m finite_ram_lab.fr_gfx_readonly_collector \
  --pid self \
  --samples 20 \
  --interval-ms 50 \
  --output self-trace.jsonl \
  --receipt self-receipt.json
```

## Self-overhead receipt

The collector records:

- wall-clock duration;
- its own process CPU time;
- one-core-equivalent CPU percentage;
- observed collector RSS;
- JSONL bytes written;
- bytes per sample.

These values are **measurements**, not qualification thresholds.

A hosted CI runner can prove the harness executes and emits the receipt.

It cannot prove that the same overhead is acceptable on a low-end gaming
machine.

That decision remains behind FR-GFX-005 A-B-A qualification.

## External graphics streams

This lane intentionally leaves:

- frame/FPS;
- Intel GPU PMU;
- DXVK backend / compiler telemetry;

as null external fields.

A later adapter should join those external streams by timestamp.

This separation matters because launching a telemetry process and reading
procfs have different perturbation costs.

## Failure semantics

If the target process disappears or procfs access is denied, collection should
fail loudly.

Missing GPU metrics in later lanes must be represented as missing values, not
zero.

## Claim ceiling

**RUNNABLE_READ_ONLY_COLLECTOR_HARNESS_ONLY**
