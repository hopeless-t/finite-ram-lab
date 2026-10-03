from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import random
import resource
import subprocess
import sys
import time
import zlib


SCHEMA = "finite-ram-lab.fr-comp-001-compressibility-surface/v0.1"

PAYLOAD_MIB = 4
REPETITIONS = 3

PAYLOADS = (
    "ZERO",
    "REPEATED_BLOCK",
    "SPARSE_OUTLIER",
    "LOW_ENTROPY_4BIT",
    "RANDOM",
)

CODECS = (
    "ZLIB_1",
    "ZLIB_9",
    "BZ2_1",
    "LZMA_0",
)


def _seed(
    payload: str,
    repetition: int,
) -> int:
    digest = hashlib.sha256(
        f"FR-COMP-001|{payload}|{repetition}".encode(
            "utf-8"
        )
    ).digest()

    return int.from_bytes(
        digest[:8],
        "big",
    )


def _payload(
    name: str,
    *,
    size_bytes: int,
    repetition: int,
) -> bytes:
    if name == "ZERO":
        return bytes(
            size_bytes
        )

    rng = random.Random(
        _seed(
            name,
            repetition,
        )
    )

    if name == "REPEATED_BLOCK":
        block = rng.randbytes(
            4096
        )

        repeats = (
            size_bytes
            // len(block)
        )

        tail = (
            size_bytes
            % len(block)
        )

        return (
            block
            * repeats
            + block[:tail]
        )

    if name == "SPARSE_OUTLIER":
        raw = bytearray(
            size_bytes
        )

        for offset in range(
            0,
            size_bytes,
            64,
        ):
            chunk = rng.randbytes(
                min(
                    8,
                    size_bytes - offset,
                )
            )

            raw[
                offset:
                offset + len(chunk)
            ] = chunk

        return bytes(
            raw
        )

    if name == "LOW_ENTROPY_4BIT":
        raw = bytearray(
            rng.randbytes(
                size_bytes
            )
        )

        for index in range(
            len(raw)
        ):
            raw[index] &= 0x0F

        return bytes(
            raw
        )

    if name == "RANDOM":
        return rng.randbytes(
            size_bytes
        )

    raise ValueError(
        f"unknown_payload:{name}"
    )


def _compress(
    codec: str,
    data: bytes,
) -> bytes:
    if codec == "ZLIB_1":
        return zlib.compress(
            data,
            level=1,
        )

    if codec == "ZLIB_9":
        return zlib.compress(
            data,
            level=9,
        )

    if codec == "BZ2_1":
        return bz2.compress(
            data,
            compresslevel=1,
        )

    if codec == "LZMA_0":
        return lzma.compress(
            data,
            preset=0,
        )

    raise ValueError(
        f"unknown_codec:{codec}"
    )


def _decompress(
    codec: str,
    data: bytes,
) -> bytes:
    if codec.startswith(
        "ZLIB_"
    ):
        return zlib.decompress(
            data
        )

    if codec.startswith(
        "BZ2_"
    ):
        return bz2.decompress(
            data
        )

    if codec.startswith(
        "LZMA_"
    ):
        return lzma.decompress(
            data
        )

    raise ValueError(
        f"unknown_codec:{codec}"
    )


def run_child(
    *,
    payload_name: str,
    codec: str,
    repetition: int,
    payload_mib: int,
) -> dict:
    size_bytes = (
        payload_mib
        * 1024
        * 1024
    )

    source = _payload(
        payload_name,
        size_bytes=size_bytes,
        repetition=repetition,
    )

    source_sha = (
        hashlib.sha256(
            source
        ).hexdigest()
    )

    wall_start = (
        time.perf_counter()
    )

    cpu_start = (
        time.process_time()
    )

    compressed = _compress(
        codec,
        source,
    )

    cpu_after_compress = (
        time.process_time()
    )

    wall_after_compress = (
        time.perf_counter()
    )

    restored = _decompress(
        codec,
        compressed,
    )

    cpu_end = (
        time.process_time()
    )

    wall_end = (
        time.perf_counter()
    )

    restored_sha = (
        hashlib.sha256(
            restored
        ).hexdigest()
    )

    if restored_sha != source_sha:
        raise RuntimeError(
            "roundtrip_digest_mismatch"
        )

    peak_rss_kib = (
        resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
    )

    return {
        "payload": payload_name,
        "codec": codec,
        "repetition": repetition,
        "source_bytes": (
            len(source)
        ),
        "compressed_bytes": (
            len(compressed)
        ),
        "compression_ratio": (
            len(compressed)
            / len(source)
        ),
        "saved_fraction": (
            1.0
            - len(compressed)
            / len(source)
        ),
        "compress_cpu_ms": (
            (
                cpu_after_compress
                - cpu_start
            )
            * 1000.0
        ),
        "compress_wall_ms": (
            (
                wall_after_compress
                - wall_start
            )
            * 1000.0
        ),
        "decompress_cpu_ms": (
            (
                cpu_end
                - cpu_after_compress
            )
            * 1000.0
        ),
        "decompress_wall_ms": (
            (
                wall_end
                - wall_after_compress
            )
            * 1000.0
        ),
        "peak_rss_kib": (
            peak_rss_kib
        ),
        "sha256": source_sha,
        "roundtrip_exact": True,
    }


def _child_command(
    *,
    payload: str,
    codec: str,
    repetition: int,
    payload_mib: int,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "finite_ram_lab.fr_compressibility_surface",
        "--child",
        "--payload",
        payload,
        "--codec",
        codec,
        "--repetition",
        str(
            repetition
        ),
        "--payload-mib",
        str(
            payload_mib
        ),
    ]


def _run_subprocess(
    *,
    payload: str,
    codec: str,
    repetition: int,
    payload_mib: int,
) -> dict:
    completed = subprocess.run(
        _child_command(
            payload=payload,
            codec=codec,
            repetition=repetition,
            payload_mib=payload_mib,
        ),
        check=True,
        text=True,
        capture_output=True,
    )

    return json.loads(
        completed.stdout
    )


def _mean(
    rows: list[float],
) -> float:
    return (
        sum(rows)
        / len(rows)
    )


def _aggregate(
    measurements: list[dict],
) -> dict:
    result = {}

    for payload in PAYLOADS:
        result[payload] = {}

        for codec in CODECS:
            rows = [
                row
                for row in measurements
                if (
                    row["payload"]
                    == payload
                    and row["codec"]
                    == codec
                )
            ]

            if len(
                rows
            ) != REPETITIONS:
                raise RuntimeError(
                    "missing_repetitions:"
                    f"{payload}:{codec}"
                )

            result[
                payload
            ][codec] = {
                "mean_compression_ratio": (
                    _mean(
                        [
                            row[
                                "compression_ratio"
                            ]
                            for row
                            in rows
                        ]
                    )
                ),
                "mean_saved_fraction": (
                    _mean(
                        [
                            row[
                                "saved_fraction"
                            ]
                            for row
                            in rows
                        ]
                    )
                ),
                "mean_compress_cpu_ms": (
                    _mean(
                        [
                            row[
                                "compress_cpu_ms"
                            ]
                            for row
                            in rows
                        ]
                    )
                ),
                "mean_decompress_cpu_ms": (
                    _mean(
                        [
                            row[
                                "decompress_cpu_ms"
                            ]
                            for row
                            in rows
                        ]
                    )
                ),
                "max_peak_rss_kib": max(
                    row[
                        "peak_rss_kib"
                    ]
                    for row
                    in rows
                ),
                "roundtrip_exact": all(
                    row[
                        "roundtrip_exact"
                    ]
                    for row
                    in rows
                ),
            }

    return result


def _pareto_codecs(
    rows: dict,
) -> list[str]:
    keys = (
        "mean_compression_ratio",
        "mean_compress_cpu_ms",
        "mean_decompress_cpu_ms",
    )

    frontier = []

    for candidate_name, candidate in (
        rows.items()
    ):
        dominated = False

        for other_name, other in (
            rows.items()
        ):
            if (
                other_name
                == candidate_name
            ):
                continue

            no_worse = all(
                other[key]
                <= candidate[key]
                for key in keys
            )

            strictly_better = any(
                other[key]
                < candidate[key]
                for key in keys
            )

            if (
                no_worse
                and strictly_better
            ):
                dominated = True
                break

        if not dominated:
            frontier.append(
                candidate_name
            )

    return sorted(
        frontier
    )


def run_experiment() -> dict:
    measurements = []

    for payload in PAYLOADS:
        for codec in CODECS:
            for repetition in range(
                REPETITIONS
            ):
                measurements.append(
                    _run_subprocess(
                        payload=payload,
                        codec=codec,
                        repetition=repetition,
                        payload_mib=(
                            PAYLOAD_MIB
                        ),
                    )
                )

    aggregate = _aggregate(
        measurements
    )

    for payload in PAYLOADS:
        for codec in CODECS:
            if not aggregate[
                payload
            ][codec][
                "roundtrip_exact"
            ]:
                raise RuntimeError(
                    "inexact_roundtrip:"
                    f"{payload}:{codec}"
                )

    zero_max = max(
        aggregate[
            "ZERO"
        ][codec][
            "mean_compression_ratio"
        ]
        for codec in CODECS
    )

    repeated_max = max(
        aggregate[
            "REPEATED_BLOCK"
        ][codec][
            "mean_compression_ratio"
        ]
        for codec in CODECS
    )

    low_entropy_min = min(
        aggregate[
            "LOW_ENTROPY_4BIT"
        ][codec][
            "mean_compression_ratio"
        ]
        for codec in CODECS
    )

    low_entropy_max = max(
        aggregate[
            "LOW_ENTROPY_4BIT"
        ][codec][
            "mean_compression_ratio"
        ]
        for codec in CODECS
    )

    random_min = min(
        aggregate[
            "RANDOM"
        ][codec][
            "mean_compression_ratio"
        ]
        for codec in CODECS
    )

    if zero_max >= 0.01:
        raise RuntimeError(
            "zero_not_highly_compressible:"
            f"{zero_max}"
        )

    if repeated_max >= 0.05:
        raise RuntimeError(
            "repeated_not_highly_compressible:"
            f"{repeated_max}"
        )

    if not (
        0.35
        <= low_entropy_min
        <= low_entropy_max
        <= 0.80
    ):
        raise RuntimeError(
            "low_entropy_surface_unexpected:"
            f"{low_entropy_min}:"
            f"{low_entropy_max}"
        )

    if random_min <= 0.98:
        raise RuntimeError(
            "random_too_compressible:"
            f"{random_min}"
        )

    summary = {}

    for payload in PAYLOADS:
        rows = aggregate[
            payload
        ]

        summary[payload] = {
            "best_ratio_codec": min(
                rows,
                key=lambda name: rows[
                    name
                ][
                    "mean_compression_ratio"
                ],
            ),
            "fastest_compress_codec": min(
                rows,
                key=lambda name: rows[
                    name
                ][
                    "mean_compress_cpu_ms"
                ],
            ),
            "fastest_decompress_codec": min(
                rows,
                key=lambda name: rows[
                    name
                ][
                    "mean_decompress_cpu_ms"
                ],
            ),
            "pareto_codecs": (
                _pareto_codecs(
                    rows
                )
            ),
            "min_compression_ratio": min(
                row[
                    "mean_compression_ratio"
                ]
                for row in rows.values()
            ),
            "max_compression_ratio": max(
                row[
                    "mean_compression_ratio"
                ]
                for row in rows.values()
            ),
        }

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "HOSTED_LINUX_GENERIC_COMPRESSIBILITY_SURFACE_VALIDATED"
        ),
        "fixture": {
            "payload_mib": (
                PAYLOAD_MIB
            ),
            "repetitions": (
                REPETITIONS
            ),
            "payloads": list(
                PAYLOADS
            ),
            "codecs": list(
                CODECS
            ),
            "fresh_process_per_measurement": (
                True
            ),
        },
        "measurements": measurements,
        "aggregate": aggregate,
        "summary": summary,
        "qualification": {
            "zero_max_ratio": (
                zero_max
            ),
            "repeated_max_ratio": (
                repeated_max
            ),
            "low_entropy_min_ratio": (
                low_entropy_min
            ),
            "low_entropy_max_ratio": (
                low_entropy_max
            ),
            "random_min_ratio": (
                random_min
            ),
        },
        "primary_findings": [
            "COMPRESSIBILITY_IS_A_PROPERTY_OF_STATE_NOT_A_CONSTANT_TIER_MULTIPLIER",
            "INCOMPRESSIBLE_STATE_CAN_CONSUME_MORE_BYTES_AFTER_CODEC_METADATA",
            "CODEC_SELECTION_IS_A_RATIO_CPU_DECODE_MEMORY_TRADEOFF",
            "COLD_STATE_CAN_RATIONALLY_USE_A_DIFFERENT_CODEC_THAN_HOT_STATE",
            "RECOMPRESSION_IS_A_REPRESENTATION_TRANSITION_NOT_FREE_CAPACITY",
            "COMPRESSED_RAM_CAPACITY_MUST_BE_ESTIMATED_FROM_THE_CURRENT_STATE_MIX",
        ],
        "boundaries": {
            "kernel": (
                "This is a userspace codec proxy, not a zram/zswap benchmark."
            ),
            "codecs": (
                "Python stdlib zlib/bz2/lzma are used for physical tradeoff measurement; kernel codec results may differ."
            ),
            "timings": (
                "Timing results are runner-specific and are not frozen as universal thresholds."
            ),
        },
        "claim_ceiling": (
            "HOSTED_LINUX_USERSPACE_CODEC_SURFACE_ONLY"
        ),
    }


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--child",
        action="store_true",
    )

    parser.add_argument(
        "--payload",
        choices=PAYLOADS,
    )

    parser.add_argument(
        "--codec",
        choices=CODECS,
    )

    parser.add_argument(
        "--repetition",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--payload-mib",
        type=int,
        default=PAYLOAD_MIB,
    )

    args = parser.parse_args(
        argv
    )

    if args.child:
        if (
            args.payload is None
            or args.codec is None
        ):
            raise ValueError(
                "child_requires_payload_and_codec"
            )

        print(
            json.dumps(
                run_child(
                    payload_name=(
                        args.payload
                    ),
                    codec=args.codec,
                    repetition=(
                        args.repetition
                    ),
                    payload_mib=(
                        args.payload_mib
                    ),
                ),
                sort_keys=True,
            )
        )

        return 0

    print(
        json.dumps(
            run_experiment(),
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
