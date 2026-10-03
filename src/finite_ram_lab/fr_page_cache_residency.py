from __future__ import annotations

import ctypes
import json
import math
import mmap
import os
from pathlib import Path
import tempfile


SCHEMA = "finite-ram-lab.fr-io-001-page-cache-residency/v0.1"
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

LIBC = ctypes.CDLL(
    None,
    use_errno=True,
)

_MINCORE = LIBC.mincore
_MINCORE.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(
        ctypes.c_ubyte
    ),
]
_MINCORE.restype = ctypes.c_int


def _resident_ratio(
    mapping: mmap.mmap,
) -> dict:
    length = len(
        mapping
    )

    pages = math.ceil(
        length
        / PAGE_SIZE
    )

    vector = (
        ctypes.c_ubyte
        * pages
    )()

    anchor = (
        ctypes.c_char
        * 1
    ).from_buffer(
        mapping
    )

    address = (
        ctypes.addressof(
            anchor
        )
    )

    rc = _MINCORE(
        ctypes.c_void_p(
            address
        ),
        ctypes.c_size_t(
            length
        ),
        vector,
    )

    if rc != 0:
        err = ctypes.get_errno()

        raise OSError(
            err,
            os.strerror(
                err
            ),
        )

    resident = sum(
        1
        for value in vector
        if value & 1
    )

    return {
        "pages": pages,
        "resident_pages": (
            resident
        ),
        "resident_fraction": (
            resident
            / pages
        ),
    }


def _touch_every_page(
    mapping: mmap.mmap,
) -> int:
    checksum = 0
    length = len(
        mapping
    )

    for offset in range(
        0,
        length,
        PAGE_SIZE,
    ):
        checksum ^= (
            mapping[offset]
        )

    checksum ^= mapping[
        length - 1
    ]

    return int(
        checksum
    )


def _drop_file_cache(
    fd: int,
) -> None:
    if not hasattr(
        os,
        "posix_fadvise",
    ):
        raise RuntimeError(
            "posix_fadvise_unavailable"
        )

    os.posix_fadvise(
        fd,
        0,
        0,
        os.POSIX_FADV_DONTNEED,
    )


def _new_file(
    path: Path,
    size_bytes: int,
) -> int:
    fd = os.open(
        path,
        (
            os.O_RDWR
            | os.O_CREAT
            | os.O_TRUNC
        ),
        0o600,
    )

    try:
        os.posix_fallocate(
            fd,
            0,
            size_bytes,
        )

        os.fsync(
            fd
        )

        _drop_file_cache(
            fd
        )

        return fd

    except BaseException:
        os.close(
            fd
        )
        raise


def _map(
    fd: int,
    size_bytes: int,
) -> mmap.mmap:
    return mmap.mmap(
        fd,
        size_bytes,
        access=mmap.ACCESS_COPY,
    )


def run_once(
    *,
    path: Path,
    size_mib: int,
) -> dict:
    size_bytes = (
        size_mib
        * 1024
        * 1024
    )

    fd = _new_file(
        path,
        size_bytes,
    )

    try:
        first = _map(
            fd,
            size_bytes,
        )

        try:
            cold = (
                _resident_ratio(
                    first
                )
            )

            checksum = (
                _touch_every_page(
                    first
                )
            )

            hot = (
                _resident_ratio(
                    first
                )
            )

        finally:
            first.close()

        _drop_file_cache(
            fd
        )

        second = _map(
            fd,
            size_bytes,
        )

        try:
            after_dontneed = (
                _resident_ratio(
                    second
                )
            )

        finally:
            second.close()

        return {
            "size_mib": (
                size_mib
            ),
            "page_size": (
                PAGE_SIZE
            ),
            "checksum": (
                checksum
            ),
            "cold": cold,
            "after_touch": hot,
            "after_fadvise_dontneed": (
                after_dontneed
            ),
        }

    finally:
        os.close(
            fd
        )


def run_experiment(
    *,
    repetitions: int = 4,
    size_mib: int = 32,
) -> dict:
    if repetitions < 1:
        raise ValueError(
            "repetitions_must_be_positive"
        )

    if size_mib < 1:
        raise ValueError(
            "size_mib_must_be_positive"
        )

    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-io-001-"
    ) as temp_dir:
        root = Path(
            temp_dir
        )

        for index in range(
            repetitions
        ):
            rows.append(
                run_once(
                    path=(
                        root
                        / f"payload-{index}.bin"
                    ),
                    size_mib=(
                        size_mib
                    ),
                )
            )

    cold = [
        row[
            "cold"
        ][
            "resident_fraction"
        ]
        for row in rows
    ]

    hot = [
        row[
            "after_touch"
        ][
            "resident_fraction"
        ]
        for row in rows
    ]

    after = [
        row[
            "after_fadvise_dontneed"
        ][
            "resident_fraction"
        ]
        for row in rows
    ]

    if max(
        cold
    ) > 0.10:
        raise RuntimeError(
            "cold_mapping_too_resident:"
            f"{cold}"
        )

    if min(
        hot
    ) < 0.95:
        raise RuntimeError(
            "touch_failed_to_materialize_pages:"
            f"{hot}"
        )

    if max(
        after
    ) > 0.25:
        raise RuntimeError(
            "dontneed_failed_to_reduce_residency:"
            f"{after}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "HOSTED_LINUX_FILE_BACKED_PAGE_CACHE_RESIDENCY_VALIDATED"
        ),
        "platform": {
            "os": "Linux",
            "page_size": (
                PAGE_SIZE
            ),
            "measurement": (
                "mincore page residency"
            ),
            "reclaim_hint": (
                "POSIX_FADV_DONTNEED"
            ),
        },
        "fixture": {
            "repetitions": (
                repetitions
            ),
            "file_size_mib": (
                size_mib
            ),
            "access": (
                "read-only page touch through ACCESS_COPY mmap"
            ),
        },
        "repetitions": rows,
        "summary": {
            "max_cold_resident_fraction": (
                max(cold)
            ),
            "min_after_touch_resident_fraction": (
                min(hot)
            ),
            "max_after_dontneed_resident_fraction": (
                max(after)
            ),
            "mean_cold_resident_fraction": (
                sum(cold)
                / len(cold)
            ),
            "mean_after_touch_resident_fraction": (
                sum(hot)
                / len(hot)
            ),
            "mean_after_dontneed_resident_fraction": (
                sum(after)
                / len(after)
            ),
        },
        "primary_findings": [
            "BACKING_LOCATION_IS_NOT_RESIDENCY_LOCATION",
            "READING_FILE_BACKED_STATE_CAN_REIMPORT_IT_INTO_RAM",
            "SSD_BACKING_DOES_NOT_BY_ITSELF_BOUND_PAGE_CACHE_RESIDENCY",
            "PAGE_CACHE_POLICY_IS_A_FIRST_CLASS_FINITE_RAM_ATOM",
            "FADVISE_DONTNEED_CAN_BE_MEASURED_AS_A_RECLAIM_HINT_BUT_IS_NOT_A_HARD_GUARANTEE",
            "OUT_OF_CORE_DESIGNS_MUST_ACCOUNT_FOR_FILE_CACHE_AND_STAGING_BYTES",
        ],
        "boundaries": {
            "fadvise_semantics": (
                "POSIX_FADV_DONTNEED is advisory; the kernel may ignore or partially satisfy advice."
            ),
            "scope": (
                "Clean temporary file-backed pages only."
            ),
            "not_tested": [
                "O_DIRECT",
                "dirty writeback",
                "MADV_COLD",
                "MADV_PAGEOUT",
                "process_madvise",
                "real model shards",
            ],
        },
        "claim_ceiling": (
            "HOSTED_LINUX_CLEAN_FILE_PAGE_CACHE_RESIDENCY_ONLY"
        ),
    }


def main() -> int:
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
