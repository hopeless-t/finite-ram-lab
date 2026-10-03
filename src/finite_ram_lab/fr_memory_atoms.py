from __future__ import annotations

import json


SCHEMA = "finite-ram-lab.fr-atom-001-memory-efficiency-periodic-table/v0.1"

ATOMS = {
    "SEMANTIC_OBLIGATION": {
        "equation_term": "S",
        "meaning": "How much information must survive for the task to remain correct/useful.",
        "current_coverage": "STRONG",
        "existing_examples": [
            "semantic working-set selection",
            "KV/prefix drop policies",
            "MoE active expert subsets",
            "bounded idiocy verification",
        ],
    },
    "REPRESENTATION_DENSITY": {
        "equation_term": "Q",
        "meaning": "Bytes required to encode each surviving unit of semantic state.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "AWQ",
            "GPTQ",
            "NF4",
            "BitNet b1.58",
            "FP8/NVFP4 source-grounded lanes",
        ],
        "gaps": [
            "activation quantization as a first-class policy",
            "KV quantization as a first-class policy",
            "codebook/additive quantization",
            "outlier sparse-high-precision escape",
            "dynamic mixed precision by state/layer/token",
            "double quantization of quantization metadata",
        ],
    },
    "RESIDENCY_FRACTION": {
        "equation_term": "R",
        "meaning": "Fraction of the chosen representation that must be physically resident now.",
        "current_coverage": "STRONG",
        "existing_examples": [
            "streamed CRT lanes",
            "RAM/compressed-RAM/SSD tiering",
            "out-of-core model shards",
            "expert hot/cold caches",
            "cloud cold tier",
            "UMA graphics residency tiers",
        ],
    },
    "DUPLICATION_FACTOR": {
        "equation_term": "D",
        "meaning": "How many physical copies of equivalent immutable or shareable state exist.",
        "current_coverage": "GAP",
        "existing_examples": [
            "Strata-Lanes shared host arena as external relative",
        ],
        "gaps": [
            "shared file-backed mmap",
            "copy-on-write sharing",
            "KSM for mergeable anonymous pages",
            "prefix/KV sharing across requests",
            "shared model/runtime arenas across workers",
        ],
    },
    "OVERLAP_CONCURRENCY": {
        "equation_term": "C",
        "meaning": "How many temporary representations/intermediates coexist at peak.",
        "current_coverage": "STRONG",
        "existing_examples": [
            "streamed vs all-resident CRT",
            "residue lane concurrency",
            "demand folding",
            "prefetch/speculation/concurrency controls",
        ],
        "gaps": [
            "general rematerialization/checkpointing model",
            "activation lifetime scheduling",
        ],
    },
    "ALLOCATOR_FRAGMENTATION": {
        "equation_term": "F",
        "meaning": "Physical memory lost to allocator slack, fragmentation, alignment, and virtual/physical layout decisions.",
        "current_coverage": "GAP",
        "gaps": [
            "PagedAttention-style block allocation",
            "virtual-memory decoupled allocation",
            "arena/slab pooling",
            "huge-page/page-table tradeoffs",
            "fragmentation telemetry",
        ],
    },
    "PAGECACHE_IO_PATH": {
        "equation_term": "P",
        "meaning": "File-cache, buffered/unbuffered IO, readahead, eviction, and backing-store interaction.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "Strata unbuffered file tier source-grounding",
            "SSD semantic tier",
            "mmap residency experiments",
        ],
        "gaps": [
            "mmap vs pread/direct-IO matched experiments",
            "page-cache pollution accounting",
            "readahead/prefetch control",
            "MADV_COLD/PAGEOUT/DONTNEED physical qualification",
        ],
    },
    "TRANSFER_STAGING": {
        "equation_term": "X",
        "meaning": "Temporary copies and buffers created while moving state between tiers/devices.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "Strata staged DMA source-grounding",
            "VRAM/GTT coupled pressure",
        ],
        "gaps": [
            "double-buffering tax",
            "pinned-memory tax",
            "zero-copy / shared-buffer experiments",
            "transfer overlap vs peak residency",
        ],
    },
    "GENERIC_COMPRESSION": {
        "equation_term": "Z",
        "meaning": "Lossless or opaque compression independent of model numeric semantics.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "zram/zswap external intake",
            "compressed-RAM semantic tier",
        ],
        "gaps": [
            "codec-dependent compression ratio/CPU/tail surface",
            "compressibility classifier",
            "compressed-page hot/cold policy",
        ],
    },
    "REMATERIALIZATION_REBUILD": {
        "equation_term": "G",
        "meaning": "Discard state and regenerate/recompute/refetch it later instead of storing it.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "drop/rebuild semantic planner",
            "streamed exact reconstruction",
            "cloud re-fetch candidate",
        ],
        "gaps": [
            "activation checkpointing/rematerialization",
            "KV discard-vs-recompute",
            "re-download-vs-cache decision model",
        ],
    },
    "DEMAND": {
        "equation_term": "W",
        "meaning": "How much concurrent work is admitted in the first place.",
        "current_coverage": "STRONG",
        "existing_examples": [
            "demand folding",
            "batch/concurrency/prefetch/speculative controls",
            "observer sampling cadence",
        ],
    },
    "TOPOLOGY": {
        "equation_term": "T",
        "meaning": "Capacity is weighted by bandwidth, latency, sharing, and failure domain.",
        "current_coverage": "PARTIAL",
        "existing_examples": [
            "VRAM/GTT/RAM coupling",
            "multi-GPU Strata relatives",
            "UMA graphics lane",
            "cloud deadline class",
        ],
        "gaps": [
            "NUMA",
            "CXL/remote memory",
            "peer/remote memory bandwidth-tail models",
        ],
    },
    "OBSERVATION": {
        "equation_term": "O",
        "meaning": "Memory and CPU consumed to measure and control the system itself.",
        "current_coverage": "STRONG",
        "existing_examples": [
            "read-only graphics observation plane",
            "signal ablation",
            "adaptive observation cadence",
            "A-B-A observer perturbation",
            "self-accounting collector",
        ],
    },
}


QUANTIZATION_COVERAGE = {
    "AWQ": "IN_GRAPH_SYNTHETIC",
    "GPTQ": "IN_GRAPH_SYNTHETIC",
    "NF4": "IN_GRAPH_SYNTHETIC",
    "GGUF": "CONTAINER_AXIS_NOT_QUANTIZER",
    "BITNET_B1_58": "NATIVE_ARCHITECTURE_CLASS",
    "FP8": "SOURCE_GROUNDED_PARTIAL",
    "NVFP4": "SOURCE_GROUNDED_PARTIAL",
    "SMOOTHQUANT_W8A8": "GAP",
    "KIVI_KV_2BIT": "GAP",
    "AQLM": "GAP",
    "QUIP_SHARP": "GAP",
    "SPQR": "GAP",
    "DYNAMIC_MIXED_PRECISION": "GAP",
    "DOUBLE_QUANT_METADATA": "GAP",
}


SOURCE_PINS = {
    "SmoothQuant": {
        "repo": "mit-han-lab/smoothquant",
        "commit": "c61476d728e42ae0d8a35e7e78494edcac3237b5",
        "role": "weight+activation quantization relative",
    },
    "KIVI": {
        "repo": "jy-yuan/KIVI",
        "commit": "876b4d2d08e3b1d5f70d0969c299d8c7c42ddfb6",
        "role": "KV-cache quantization relative",
    },
    "AQLM": {
        "repo": "Vahe1994/AQLM",
        "commit": "e79a896ed6656fe4ed06193d42d004e7d0bbdbb2",
        "role": "2-3 bit additive/codebook quantization relative",
    },
    "QuIPSharp": {
        "repo": "Cornell-RelaxML/quip-sharp",
        "commit": "1d8f873e9a2a8b86b12bb1064c312c5689b77d98",
        "role": "extreme codebook/incoherence PTQ relative",
    },
    "SpQR": {
        "repo": "Vahe1994/SpQR",
        "commit": "543d10e56f921e5eeb10d5f0aaaccd30b6662d0e",
        "role": "outlier sparse-quantized representation relative",
    },
    "vLLM": {
        "repo": "vllm-project/vllm",
        "commit": "5f30fc7031cae49bf51073fc953d419b08f8887c",
        "role": "paged KV allocation/sharing relative",
    },
}


def memory_equation() -> dict:
    return {
        "physical_peak": (
            "M_peak ~= sum_i(S_i * Q_i * R_i * D_i * C_i) + F + P + X + Z_meta + O"
        ),
        "terms": {
            "S": "semantic obligation",
            "Q": "representation bytes per semantic unit",
            "R": "resident fraction",
            "D": "duplication factor",
            "C": "overlap/concurrency multiplier",
            "F": "allocator/fragmentation slack",
            "P": "page-cache/backing-path footprint",
            "X": "transfer/staging buffers",
            "Z_meta": "compression/quantization metadata and workspaces",
            "O": "observation/control overhead",
        },
        "warning": (
            "The multiplicative core is an accounting abstraction; terms may interact and must be measured locally."
        ),
    }


def immediate_priorities() -> list[dict]:
    return [
        {
            "rank": 1,
            "atom": "DUPLICATION_FACTOR",
            "experiment": "FR-SHARE-001",
            "reason": (
                "Multiple workers can erase quantization gains if immutable state is physically copied. Measure private copies vs shared file-backed mappings before pursuing another bit-width."
            ),
        },
        {
            "rank": 2,
            "atom": "ALLOCATOR_FRAGMENTATION",
            "experiment": "FR-ALLOC-001",
            "reason": (
                "PagedAttention/vAttention show that dynamic-state fragmentation and duplication can waste memory independent of numeric precision."
            ),
        },
        {
            "rank": 3,
            "atom": "REPRESENTATION_DENSITY",
            "experiment": "FR-QUANT-002",
            "reason": (
                "Promote activation/KV/extreme-codebook/mixed-precision quantization to first-class controller choices rather than source notes."
            ),
        },
        {
            "rank": 4,
            "atom": "REMATERIALIZATION_REBUILD",
            "experiment": "FR-REMAT-001",
            "reason": (
                "Trade recomputation for storage explicitly; activation checkpointing provides a known memory-compute frontier."
            ),
        },
        {
            "rank": 5,
            "atom": "PAGECACHE_IO_PATH",
            "experiment": "FR-IO-001",
            "reason": (
                "File-backed out-of-core state can consume RAM through page cache or staging even when nominally placed on SSD."
            ),
        },
        {
            "rank": 6,
            "atom": "GENERIC_COMPRESSION",
            "experiment": "FR-COMP-001",
            "reason": (
                "Compressed RAM needs a codec/cost model, not a single abstract compressed tier."
            ),
        },
        {
            "rank": 7,
            "atom": "TOPOLOGY",
            "experiment": "FR-TOPO-001",
            "reason": (
                "NUMA/CXL/remote capacity can be physically large but deadline-poor; topology must stay typed."
            ),
        },
    ]


def run_panel() -> dict:
    gap_atoms = [
        name
        for name, row
        in ATOMS.items()
        if row[
            "current_coverage"
        ] == "GAP"
    ]

    partial_atoms = [
        name
        for name, row
        in ATOMS.items()
        if row[
            "current_coverage"
        ] == "PARTIAL"
    ]

    strong_atoms = [
        name
        for name, row
        in ATOMS.items()
        if row[
            "current_coverage"
        ] == "STRONG"
    ]

    required_quant = {
        "AWQ",
        "GPTQ",
        "NF4",
        "GGUF",
        "BITNET_B1_58",
    }

    if not required_quant.issubset(
        QUANTIZATION_COVERAGE
    ):
        raise RuntimeError(
            "foundational_quantization_taxonomy_missing"
        )

    if (
        QUANTIZATION_COVERAGE[
            "GGUF"
        ]
        != "CONTAINER_AXIS_NOT_QUANTIZER"
    ):
        raise RuntimeError(
            "gguf_misclassified"
        )

    if (
        immediate_priorities()[0][
            "atom"
        ]
        != "DUPLICATION_FACTOR"
    ):
        raise RuntimeError(
            "priority_order_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "MEMORY_EFFICIENCY_ATOMIC_INVENTORY_FROZEN"
        ),
        "equation": (
            memory_equation()
        ),
        "atoms": ATOMS,
        "coverage_summary": {
            "strong": (
                strong_atoms
            ),
            "partial": (
                partial_atoms
            ),
            "gap": gap_atoms,
        },
        "quantization_coverage": (
            QUANTIZATION_COVERAGE
        ),
        "source_pins": (
            SOURCE_PINS
        ),
        "immediate_priorities": (
            immediate_priorities()
        ),
        "primary_findings": [
            "QUANTIZATION_IS_ONLY_ONE_MULTIPLIER_IN_PEAK_MEMORY",
            "DUPLICATION_CAN_ERASE_REPRESENTATION_SAVINGS",
            "ALLOCATOR_FRAGMENTATION_IS_AN_INDEPENDENT_MEMORY_ATOM",
            "REMATERIALIZATION_TRADES_COMPUTE_FOR_RESIDENCY",
            "PAGE_CACHE_AND_STAGING_CAN_REIMPORT_NOMINALLY_OFFLOADED_BYTES_INTO_RAM",
            "OBSERVATION_OVERHEAD_BELONGS_IN_THE_MEMORY_EQUATION",
            "THE_NEXT_HIGH_LEVERAGE_GAP_IS_SHARING_NOT_ANOTHER_WEIGHT_ONLY_QUANTIZER",
        ],
        "claim_ceiling": (
            "SOURCE_GROUNDED_ATOMIC_INVENTORY_AND_RESEARCH_PRIORITIZATION_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
