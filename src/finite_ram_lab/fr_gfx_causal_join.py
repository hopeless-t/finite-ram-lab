from __future__ import annotations

import argparse
import bisect
import json
from pathlib import Path


SCHEMA = "finite-ram-lab.fr-gfx-007-causal-sidecar-join/v0.1"


def _load_jsonl(
    path: Path,
) -> list[dict]:
    rows = []

    for raw in path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw.strip()

        if not line:
            continue

        rows.append(
            json.loads(
                line
            )
        )

    return rows


def _timestamps(
    rows: list[dict],
) -> list[int]:
    result = []

    previous = None

    for row in rows:
        value = int(
            row[
                "timestamp_monotonic_ns"
            ]
        )

        if (
            previous is not None
            and value < previous
        ):
            raise ValueError(
                "sidecar_not_sorted"
            )

        result.append(
            value
        )
        previous = value

    return result


def causal_asof(
    *,
    timestamp_ns: int,
    rows: list[dict],
    timestamps: list[int],
    max_age_ns: int,
) -> dict:
    if max_age_ns < 0:
        raise ValueError(
            "max_age_ns_negative"
        )

    index = (
        bisect.bisect_right(
            timestamps,
            timestamp_ns,
        )
        - 1
    )

    if index < 0:
        return {
            "value": None,
            "missing": True,
            "stale": False,
            "age_ns": None,
            "source_timestamp_ns": None,
        }

    source = rows[index]
    source_timestamp = (
        timestamps[index]
    )

    if source_timestamp > timestamp_ns:
        raise RuntimeError(
            "future_leakage"
        )

    age = (
        timestamp_ns
        - source_timestamp
    )

    if age > max_age_ns:
        return {
            "value": None,
            "missing": False,
            "stale": True,
            "age_ns": age,
            "source_timestamp_ns": (
                source_timestamp
            ),
        }

    return {
        "value": source,
        "missing": False,
        "stale": False,
        "age_ns": age,
        "source_timestamp_ns": (
            source_timestamp
        ),
    }


def join_records(
    *,
    base_rows: list[dict],
    frame_rows: list[dict],
    gpu_rows: list[dict],
    backend: dict,
    frame_max_age_ns: int,
    gpu_max_age_ns: int,
) -> list[dict]:
    frame_ts = _timestamps(
        frame_rows
    )

    gpu_ts = _timestamps(
        gpu_rows
    )

    output = []

    for base in base_rows:
        timestamp_ns = int(
            base[
                "timestamp_monotonic_ns"
            ]
        )

        frame = causal_asof(
            timestamp_ns=timestamp_ns,
            rows=frame_rows,
            timestamps=frame_ts,
            max_age_ns=(
                frame_max_age_ns
            ),
        )

        gpu = causal_asof(
            timestamp_ns=timestamp_ns,
            rows=gpu_rows,
            timestamps=gpu_ts,
            max_age_ns=(
                gpu_max_age_ns
            ),
        )

        row = dict(base)

        row[
            "joined_evidence"
        ] = {
            "frame": frame,
            "gpu": gpu,
            "backend": {
                "value": backend,
                "missing": False,
                "stale": False,
                "age_ns": None,
                "source_timestamp_ns": None,
            },
        }

        output.append(row)

    return output


def _synthetic_fixture() -> dict:
    base = [
        {
            "timestamp_monotonic_ns": (
                1_000
            ),
            "id": "B1",
        },
        {
            "timestamp_monotonic_ns": (
                2_000
            ),
            "id": "B2",
        },
        {
            "timestamp_monotonic_ns": (
                3_000
            ),
            "id": "B3",
        },
        {
            "timestamp_monotonic_ns": (
                4_000
            ),
            "id": "B4",
        },
    ]

    frames = [
        {
            "timestamp_monotonic_ns": (
                900
            ),
            "frametime_ms": 100.0,
        },
        {
            "timestamp_monotonic_ns": (
                1_900
            ),
            "frametime_ms": 80.0,
        },
        {
            "timestamp_monotonic_ns": (
                3_100
            ),
            "frametime_ms": 70.0,
        },
        {
            "timestamp_monotonic_ns": (
                3_950
            ),
            "frametime_ms": 65.0,
        },
    ]

    gpu = [
        {
            "timestamp_monotonic_ns": (
                500
            ),
            "render_busy_pct": 88.0,
        },
        {
            "timestamp_monotonic_ns": (
                2_500
            ),
            "render_busy_pct": 96.0,
        },
    ]

    joined = join_records(
        base_rows=base,
        frame_rows=frames,
        gpu_rows=gpu,
        backend={
            "translation": "DXVK",
            "api": "D3D11",
        },
        frame_max_age_ns=500,
        gpu_max_age_ns=1_000,
    )

    return {
        "base": base,
        "frame": frames,
        "gpu": gpu,
        "joined": joined,
    }


def run_panel() -> dict:
    fixture = (
        _synthetic_fixture()
    )

    rows = fixture[
        "joined"
    ]

    b1 = rows[0][
        "joined_evidence"
    ]

    b2 = rows[1][
        "joined_evidence"
    ]

    b3 = rows[2][
        "joined_evidence"
    ]

    b4 = rows[3][
        "joined_evidence"
    ]

    if (
        b1["frame"][
            "source_timestamp_ns"
        ]
        != 900
    ):
        raise RuntimeError(
            "b1_frame_wrong"
        )

    if (
        b2["frame"][
            "source_timestamp_ns"
        ]
        != 1900
    ):
        raise RuntimeError(
            "b2_frame_wrong"
        )

    if not (
        b3["frame"][
            "stale"
        ]
        and b3[
            "frame"
        ]["value"]
        is None
        and b3[
            "frame"
        ][
            "source_timestamp_ns"
        ]
        == 1900
    ):
        raise RuntimeError(
            "b3_future_frame_leaked"
        )

    if (
        b4["frame"][
            "source_timestamp_ns"
        ]
        != 3950
    ):
        raise RuntimeError(
            "b4_frame_wrong"
        )

    if (
        b1["gpu"][
            "source_timestamp_ns"
        ]
        != 500
    ):
        raise RuntimeError(
            "b1_gpu_wrong"
        )

    if not (
        b2["gpu"][
            "stale"
        ]
        and b2[
            "gpu"
        ]["value"]
        is None
    ):
        raise RuntimeError(
            "b2_stale_gpu_not_rejected"
        )

    if (
        b3["gpu"][
            "source_timestamp_ns"
        ]
        != 2500
    ):
        raise RuntimeError(
            "b3_gpu_wrong"
        )

    if not (
        b4["gpu"][
            "stale"
        ]
        and b4[
            "gpu"
        ]["value"]
        is None
    ):
        raise RuntimeError(
            "b4_stale_gpu_not_rejected"
        )

    future_leakage_count = 0

    for row in rows:
        target = row[
            "timestamp_monotonic_ns"
        ]

        for key in (
            "frame",
            "gpu",
        ):
            evidence = row[
                "joined_evidence"
            ][key]

            source_ts = evidence[
                "source_timestamp_ns"
            ]

            if (
                source_ts is not None
                and source_ts
                > target
            ):
                future_leakage_count += 1

    if future_leakage_count:
        raise RuntimeError(
            "future_leakage_detected"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "CAUSAL_ASOF_SIDECAR_JOIN_VALIDATED"
        ),
        "fixture": fixture,
        "invariants": {
            "latest_known_only": True,
            "future_leakage_count": (
                future_leakage_count
            ),
            "stale_is_not_zero": True,
            "missing_is_not_zero": True,
            "backend_identity_is_explicit": True,
        },
        "join_rule": (
            "select max(source_timestamp)<=target_timestamp; reject if age>max_age"
        ),
        "primary_findings": [
            "NEAREST_NEIGHBOR_JOIN_IS_NOT_SAFE_FOR_LIVE_REPLAY",
            "FUTURE_EVIDENCE_MUST_NEVER_BE_ATTACHED_TO_PAST_CONTROL_STATE",
            "STALE_EVIDENCE_MUST_BE_DISTINGUISHED_FROM_MISSING_EVIDENCE",
            "MISSING_OR_STALE_GPU_COUNTERS_MUST_NOT_BE_COERCED_TO_ZERO",
            "BACKEND_IDENTITY_BELONGS_IN_EVERY_REPLAY_RECORD",
        ],
        "claim_ceiling": (
            "CAUSAL_OFFLINE_JOIN_CONTRACT_ONLY"
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


def cli(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base",
        required=True,
    )

    parser.add_argument(
        "--frame",
        required=True,
    )

    parser.add_argument(
        "--gpu",
        required=True,
    )

    parser.add_argument(
        "--backend",
        required=True,
    )

    parser.add_argument(
        "--frame-max-age-ms",
        type=float,
        default=250.0,
    )

    parser.add_argument(
        "--gpu-max-age-ms",
        type=float,
        default=750.0,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args(
        argv
    )

    base = _load_jsonl(
        Path(args.base)
    )

    frame = _load_jsonl(
        Path(args.frame)
    )

    gpu = _load_jsonl(
        Path(args.gpu)
    )

    backend = json.loads(
        Path(args.backend)
        .read_text(
            encoding="utf-8"
        )
    )

    joined = join_records(
        base_rows=base,
        frame_rows=frame,
        gpu_rows=gpu,
        backend=backend,
        frame_max_age_ns=int(
            args.frame_max_age_ms
            * 1_000_000
        ),
        gpu_max_age_ns=int(
            args.gpu_max_age_ms
            * 1_000_000
        ),
    )

    output = Path(
        args.output
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        "".join(
            json.dumps(
                row,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
            )
            + "\n"
            for row in joined
        ),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
