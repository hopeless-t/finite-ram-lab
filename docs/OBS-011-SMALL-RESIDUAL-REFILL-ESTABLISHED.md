# OBS-011 — SMALL_RESIDUAL_REFILL establishment

## Result

`SMALL_RESIDUAL_REFILL` is promoted from candidate to an established Chapter-II mechanism.

Physical run:

- experiment: `TX-SMALL-RESIDUAL-REFILL1-CAPTURE-v1`
- run: `36697763027`
- launch commit: `94801d89b751482fff71c8761c9c71c80c66e35b`
- stage size: 32 fresh CPUSET_PREP_ONLY identities
- workflow conclusion: success
- promoted specimens: 2

Aggregate:

```text
T1_NO_OWNER_REFILL1                  29
SMALL_RESIDUAL_REFILL_ESTABLISHMENT  2
INVALID_OBSERVER                      1
```

First-Q64 histogram:

```text
T=1  29
T=2   2
```

## Promoted specimens

Trials `1:4` and `2:7` independently satisfy the frozen promotion rule.

For both specimens:

- startup cgroup cpuset was restricted to the prep CPU;
- after READY the cpuset was expanded to prep + stock CPU;
- the target cgroup contained only the final worker process;
- PTE, CPU, worker-sequence and trace guards were clean;
- premeasurement refill probe missed count was zero;
- all measured Q64/refill63 windows had zero missed hits;
- no owner refill63 was observed on the stock CPU in the current premeasurement epoch;
- exactly one owner-memcg `refill_stock(...,1)` was observed on the future stock CPU;
- the emitter was `systemd` PID 1;
- the first measured direct Q64 occurred at touch 2;
- therefore the inferred natural residual was `S0=1`.

The repeated physical sequence is:

```text
systemd PID1 on future stock CPU
  -> refill_stock(owner_memcg, 1)
  -> natural pre-VERIFY residual S0=1
  -> first measured direct Q64 at T=2
```

Because this sequence was captured twice with zero missed hits on all critical intervals, mechanism existence is now established.

## Why this is distinct from STARTUP_STOCK_SEED

`STARTUP_STOCK_SEED` is the large-residual path:

```text
startup Q64
  -> refill63
  -> S0 roughly 43..48 in captured specimens
  -> T roughly 44..49
```

The cpuset intervention suppresses that phenotype.

`SMALL_RESIDUAL_REFILL` survives as a separate small-state path:

```text
no stock-CPU owner refill63 in the current premeasurement epoch
  -> owner refill1
  -> S0=1
  -> T=2
```

The two mechanisms must not be merged into one generic startup-noise label.

## Observer lesson

R13-A initially used a broad continuously-active refill observer and suffered both probe misses and a retrospective scope defect.

R13-B1 changed the observer contract:

- the refill probe was enabled only during the short premeasurement epoch;
- the same refill probe was switched to target-only refill63 during measured touch windows;
- Q64 was enabled only during measured touch windows;
- retrospective ownership matching was bounded to the current trial.

This reduced the evidence problem enough to produce two zero-miss promoted specimens in the first 32-identity stage.

## Source compatibility

Linux `refill_stock()` has source paths that can return arbitrary small page counts to per-CPU memcg stock without a contemporaneous direct Q64, including:

- `obj_cgroup_uncharge_pages()`;
- `mem_cgroup_sk_uncharge()`;
- charge-excess return through `try_charge_memcg()`.

The next experiment must identify which call path produced the systemd PID1 refill1 receipts.

## Evidence

Raw evidence manifest:

- files: 84
- bytes: 3,263,807
- content-set SHA-256: `927593f98e4d532ab045a563b206e98ffc454c85c2eff190c8481f06b7243f34`
- created: `2026-09-30T09:43:17Z`

Aggregate artifact:

- ID: `11087599946`
- digest: `sha256:a0f7f3dea075b98f96c6aedf8f11555dc7d32b45d6cd6a14a75004b56cf7b51e`

Machine-readable freeze:

- `analysis/inputs/SMALL-RESIDUAL-REFILL1-CAPTURE-STAGE1-PHYSICAL-RESULT-v1.json`

## Next

R13-B2 should observe only the short STARTUP refill1 window with conditional stack capture, then resolve the caller path for a zero-miss owner refill1 specimen.

Candidate provenance classes:

- `OBJCG_UNCHARGE_REFILL1`
- `SOCKET_UNCHARGE_REFILL1`
- `TRY_CHARGE_EXCESS_REFILL1`
- `OTHER_REFILL1_CALLER`

Mechanism existence is established regardless of which provenance class wins.

## Claim ceiling

This result establishes the existence of the small-residual state transition in the measured hosted environment.

It does not estimate prevalence and does not certify transactional reliability.
