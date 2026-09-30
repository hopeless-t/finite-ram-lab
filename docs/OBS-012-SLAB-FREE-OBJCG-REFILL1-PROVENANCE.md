# OBS-012 — Refill1 provenance resolved to slab-free objcg uncharge

## Physical source

Experiment:

`TX-SMALL-RESIDUAL-REFILL1-PROVENANCE-v1`

Run:

`36699038147`

The frozen physical aggregate remains unchanged:

- 32 trials
- 27 valid under the frozen observer contract
- one `PROVENANCE_CAPTURED` specimen
- trial `1:7`
- frozen automatic provenance class: `OTHER_REFILL1_CALLER`

The old classifier did not recognize the source-grounded slab-free objcg path.

## Trial 1:7

The zero-miss physical specimen has:

```text
T = 2
S0 = 1
owner refill1 count = 1
startup refill probe missed = 0
measured Q64/refill63 missed = 0
emitter = systemd PID1
CPU = future stock CPU
```

Observed stack:

```text
refill_stock
__memcg_slab_free_hook
kfree
skb_free_head
skb_release_data
consume_skb
skb_free_datagram
__unix_dgram_recvmsg
unix_dgram_recvmsg
sock_recvmsg
...
systemd userspace syscall return
```

## Source-grounded call chain

In the examined Linux source, `__memcg_slab_free_hook()` frees an accounted slab object and calls:

```text
__refill_obj_stock(objcg, stock, obj_size, true)
```

That helper accumulates freed object bytes.

When the accumulated byte credit crosses a page boundary with uncharge allowed, it computes:

```text
nr_pages = stock_nr_bytes >> PAGE_SHIFT
```

and calls:

```text
obj_cgroup_uncharge_pages(objcg, nr_pages)
```

`obj_cgroup_uncharge_pages()` resolves the owning memcg and returns those pages to the per-CPU memcg stock through:

```text
refill_stock(memcg, nr_pages)
```

For trial `1:7`, the physical event has `nr_pages=1`.

Therefore the provenance is resolved as:

```text
SLAB_FREE_OBJCG_REFILL1
  subset of OBJCG_UNCHARGE_REFILL1
```

The intermediate static helper frames need not appear separately in the runtime stack for the source chain to be identified: the observed caller frame is `__memcg_slab_free_hook`, and its source path to `refill_stock` passes through the objcg uncharge machinery.

## Concrete mechanism

The physical/source chain is:

```text
systemd receives a UNIX datagram
  -> skb data/head freed
  -> kfree
  -> __memcg_slab_free_hook
  -> objcg byte stock crosses one-page uncharge boundary
  -> obj_cgroup_uncharge_pages(...,1)
  -> refill_stock(owner_memcg,1)
  -> natural pre-VERIFY S0=1
  -> first measured direct Q64 at T=2
```

This explains how a one-page memcg stock residual can appear without a contemporaneous direct Q64.

## Status

`SMALL_RESIDUAL_REFILL` remains established.

Caller provenance for trial `1:7` is now source-grounded:

`SLAB_FREE_OBJCG_REFILL1`.

Do not rewrite the frozen Stage-1 physical aggregate. The source-grounded classification is a separate replay.

## Research boundary

This closes the immediate pre-VERIFY provenance question strongly enough to stop expanding that taxonomy.

The next frontier returns to the already-frozen verified-state age-decoupling experiment.

## Evidence

Physical freeze:

- `analysis/inputs/REFILL1-PROVENANCE-STAGE1-PHYSICAL-RESULT-v1.json`

Source-grounded replay:

- `analysis/inputs/REFILL1-PROVENANCE-SOURCE-REPLAY-v1.json`

Raw manifest:

- files: 84
- bytes: 25,081,990
- content-set SHA-256: `3c8ddfa552036917db315f3a797f79c673e8659d924b53bcbaa24e0bb73ff247`

Aggregate artifact:

- ID: `11089576790`
- digest: `sha256:bec9236cb19603d6822ac24c2a14ca6197e425f1854afc23480f3b9ca8ba0adf`

## Claim ceiling

This resolves caller provenance for one complete zero-miss physical specimen.

It does not estimate prevalence and does not certify transactional reliability.
