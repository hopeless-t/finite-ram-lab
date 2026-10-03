# FR-ALLOC-001 — Fragmentation and Prefix-Sharing Surface

Status: **SOURCE-GROUNDED SYNTHETIC ALLOCATOR EXPERIMENT**

Parent: **FR-QUANT-002**

## Question

After reducing representation density and duplicate copies, how much memory is
still lost purely because state is laid out badly?

This lane isolates allocator geometry.

## Source relatives

### PagedAttention / vLLM

PagedAttention was introduced to address large, dynamically growing KV caches
whose capacity was wasted by fragmentation and redundant duplication.

The core transfer is:

- allocate physical KV capacity on demand;
- permit non-contiguous physical blocks;
- share reusable KV blocks across compatible requests.

Current vLLM implementation details have evolved, so this lane transfers the
invariant rather than claiming to reproduce current vLLM internals.

Pinned source:

`vllm-project/vllm@5f30fc7031cae49bf51073fc953d419b08f8887c`

### vAttention

vAttention exposes a second important design point:

> physical allocation can be on-demand while the virtual KV address space
> remains contiguous.

It uses CUDA virtual-memory APIs to separate virtual layout from physical
allocation and highlights that paged user-space layouts have their own block
table / kernel costs.

Pinned source:

`microsoft/vattention@71a0e91aa46ff8fa985bcca3327efe0ab9929a39`

FR-ALLOC-001 does not benchmark either implementation.

## Dynamic synthetic pool

The frozen simulator has:

- 512 physical blocks;
- 5,000 ticks;
- 5,280 deterministic requests;
- request sizes from 2 to 32 blocks;
- finite lifetimes;
- 12 repeated-prefix groups;
- 70% chance of a reusable four-block prefix.

Four allocator policies see the exact same event trace.\n\nReproducibility freezes both the seed and draw-domain labels. An initial pilot used different domain labels; the repository implementation is canonical and no qualification threshold was relaxed.

## 1. MAX_RESERVE

Each request reserves the maximum possible 32 blocks.

Result:

- admitted: **1,839**
- rejected: **3,441**

This is capacity stranding by reservation.

It is the memory analogue of allocating every request for its worst-case future
length.

## 2. CONTIG_FIRST_FIT

Each request allocates only its actual size, but requires a physically
contiguous run.

Result:

- admitted: **4,685**
- rejected: **595**
- rejects with enough total free blocks but no large enough contiguous run:
  **590**

Thus:

[
rac{590}{595}
=
99.1597%.
]

Almost every rejection is external fragmentation rather than true exhaustion.

This gives a concrete form to:

[
oxed{
	ext{total free capacity}

eq
	ext{allocatable capacity}
}
]

## 3. PAGED

The same requests can use arbitrary free physical blocks.

Result:

- admitted: **4,787**
- rejected: **493**

No semantic bytes were reduced.

No quantization was changed.

The improvement comes only from removing the contiguous-allocation constraint.

## 4. PAGED_PREFIX_SHARE

After external fragmentation is removed, equivalent prefix blocks are shared
across compatible requests.

Result:

- admitted: **5,056**
- rejected: **224**
- duplicate prefix blocks avoided over the trace: **12,904**

Compared with plain PAGED:

[
504ightarrow241
]

or roughly **54.56% fewer rejects**.

This is the interaction:

[
oxed{
F 	ext{ first, then } D
}
]

where (F) is fragmentation and (D) is duplication.

## Internal fragmentation: block size matters too

Paging removes external fragmentation but introduces a granularity decision.

For 8,192 deterministic request lengths from 1–2,048 tokens:

| block size | internal waste |
|---:|---:|
| 8 tokens | 0.3401% |
| 16 | 0.7225% |
| 32 | 1.4897% |
| 64 | 2.9718% |
| 128 | 5.7859% |

Smaller blocks reduce internal waste.

But smaller blocks can increase:

- block-table entries;
- allocator operations;
- metadata;
- kernel address translation/gather work.

Therefore the smallest block is not automatically optimal.

The missing objective is:

[
min
(
	ext{internal waste}
+
	ext{allocator metadata}
+
	ext{kernel/layout cost}
+
	ext{allocation latency}
).
]

## Interaction with quantization

Quantization shrinks the size of each block.

Allocation changes whether those blocks can actually be packed and shared.

So:

[
oxed{
Q 	imes D 	imes F
}
]

must be measured jointly.

A perfectly quantized representation can still waste memory if:

- each worker has its own copy;
- requests reserve future capacity;
- free memory is fragmented;
- shared prefixes are duplicated.

## New Finite RAM rule

The earlier rule was:

> Count effective bits, not the quantization label.

Now add:

> Count **allocatable bytes**, not just free bytes.

## Next

### FR-ALLOC-002 — allocator × quantization × sharing factorial

Sweep:

- representation density;
- worker/request count;
- prefix reuse;
- block granularity;
- pool pressure.

Endpoints:

- admitted work;
- internal waste;
- external fragmentation;
- duplicate bytes;
- allocator metadata;
- semantic/task survival.

### FR-REMAT-001

After representation, duplication and allocation have been separated, attack
the next atom:

`retain vs recompute/rebuild`.

## Claim ceiling

**SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY**
