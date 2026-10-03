from __future__ import annotations

import gc
import json
import mmap
import os
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-010-hosted-residency/v0.1"

STATE_MIB = 8
STATE_BYTES = STATE_MIB * 1024 * 1024
STEPS = 12
SAFE_STEP = 6


def _status_kib() -> dict[str, int]:
    wanted = {
        "VmRSS": "vmrss_kib",
        "RssAnon": "rssanon_kib",
        "RssFile": "rssfile_kib",
        "RssShmem": "rssshmem_kib",
    }
    out = {
        value: 0
        for value
        in wanted.values()
    }

    for line in Path(
        f"/proc/{os.getpid()}/status"
    ).read_text(
        encoding="utf-8"
    ).splitlines():
        key = line.split(
            ":",
            1,
        )[0]

        if key in wanted:
            parts = line.split()

            if len(parts) >= 2:
                out[
                    wanted[key]
                ] = int(
                    parts[1]
                )

    return out


def _fault_state(
    marker: int,
) -> mmap.mmap:
    region = mmap.mmap(
        -1,
        STATE_BYTES,
        flags=(
            mmap.MAP_PRIVATE
            | mmap.MAP_ANONYMOUS
        ),
        prot=(
            mmap.PROT_READ
            | mmap.PROT_WRITE
        ),
    )

    page_size = os.sysconf(
        "SC_PAGE_SIZE"
    )

    value = marker % 251 + 1

    for offset in range(
        0,
        STATE_BYTES,
        page_size,
    ):
        region[
            offset
        ] = value

    return region


def _close_all(
    regions: list[mmap.mmap],
) -> None:
    for region in regions:
        try:
            region.close()
        except Exception:
            pass

    regions.clear()
    gc.collect()
    time.sleep(
        0.01
    )


def run_arm(
    policy: str,
) -> dict[str, Any]:
    if policy not in {
        "FULL_TRAJECTORY",
        "GATED_ENDPOINT",
    }:
        raise ValueError(
            f"unknown_policy:{policy}"
        )

    regions: list[
        mmap.mmap
    ] = []

    baseline = _status_kib()
    peak_rss = baseline[
        "vmrss_kib"
    ]
    peak_anon = baseline[
        "rssanon_kib"
    ]
    peak_live_states = 0
    trace = []
    endpoint_mode = False

    try:
        for step in range(
            1,
            STEPS + 1,
        ):
            regions.append(
                _fault_state(
                    step
                )
            )

            pre_action = (
                _status_kib()
            )

            peak_rss = max(
                peak_rss,
                pre_action[
                    "vmrss_kib"
                ],
            )
            peak_anon = max(
                peak_anon,
                pre_action[
                    "rssanon_kib"
                ],
            )
            peak_live_states = max(
                peak_live_states,
                len(regions),
            )

            action = (
                "RETAIN"
            )

            if (
                policy
                == "GATED_ENDPOINT"
                and (
                    step >= SAFE_STEP
                    or endpoint_mode
                )
            ):
                endpoint_mode = True
                old = regions[:-1]
                current = regions[-1]
                regions = [
                    current
                ]

                for region in old:
                    region.close()

                gc.collect()
                time.sleep(
                    0.005
                )
                action = (
                    "CLOSE_OLD_STATES"
                )

            post_action = (
                _status_kib()
            )

            peak_rss = max(
                peak_rss,
                post_action[
                    "vmrss_kib"
                ],
            )
            peak_anon = max(
                peak_anon,
                post_action[
                    "rssanon_kib"
                ],
            )

            trace.append(
                {
                    "step": step,
                    "action": action,
                    "live_states": (
                        len(regions)
                    ),
                    "pre_action": (
                        pre_action
                    ),
                    "post_action": (
                        post_action
                    ),
                }
            )

        final = _status_kib()

        return {
            "policy": policy,
            "baseline": baseline,
            "final_before_cleanup": (
                final
            ),
            "peak_rss_kib": (
                peak_rss
            ),
            "peak_rss_delta_kib": (
                peak_rss
                - baseline[
                    "vmrss_kib"
                ]
            ),
            "peak_rssanon_kib": (
                peak_anon
            ),
            "peak_rssanon_delta_kib": (
                peak_anon
                - baseline[
                    "rssanon_kib"
                ]
            ),
            "final_rss_delta_kib": (
                final[
                    "vmrss_kib"
                ]
                - baseline[
                    "vmrss_kib"
                ]
            ),
            "peak_live_states": (
                peak_live_states
            ),
            "final_live_states": (
                len(regions)
            ),
            "trace": trace,
        }

    finally:
        _close_all(
            regions
        )


def run_panel() -> dict[str, Any]:
    full = run_arm(
        "FULL_TRAJECTORY"
    )
    gated = run_arm(
        "GATED_ENDPOINT"
    )

    expected_full_kib = (
        STATE_MIB
        * STEPS
        * 1024
    )

    physical_ratio = (
        gated[
            "peak_rss_delta_kib"
        ]
        / full[
            "peak_rss_delta_kib"
        ]
    )

    checks = {
        "full_faulted_material_residency": (
            full[
                "peak_rss_delta_kib"
            ]
            > 0.70
            * expected_full_kib
        ),
        "full_keeps_all_states": (
            full[
                "peak_live_states"
            ]
            == STEPS
            and full[
                "final_live_states"
            ]
            == STEPS
        ),
        "gated_peak_matches_semantic_frontier": (
            gated[
                "peak_live_states"
            ]
            == SAFE_STEP
            and gated[
                "final_live_states"
            ]
            == 1
        ),
        "gated_peak_rss_materially_lower": (
            physical_ratio
            < 0.70
        ),
        "gated_final_rss_lower_than_full_final": (
            gated[
                "final_rss_delta_kib"
            ]
            < full[
                "final_rss_delta_kib"
            ]
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "HOSTED_LINUX_ANONYMOUS_MMAP_RESIDENCY_LIFECYCLE"
        ),
        "environment": {
            "platform": (
                os.uname().sysname
            ),
            "release": (
                os.uname().release
            ),
            "page_size": (
                os.sysconf(
                    "SC_PAGE_SIZE"
                )
            ),
            "github_actions": (
                os.getenv(
                    "GITHUB_ACTIONS"
                )
                == "true"
            ),
        },
        "fixture": {
            "state_mib": (
                STATE_MIB
            ),
            "steps": STEPS,
            "safe_step": (
                SAFE_STEP
            ),
            "full_logical_peak_mib": (
                STATE_MIB
                * STEPS
            ),
            "gated_logical_peak_mib": (
                STATE_MIB
                * SAFE_STEP
            ),
        },
        "full": full,
        "gated": gated,
        "physical_peak_ratio_gated_over_full": (
            physical_ratio
        ),
        "checks": checks,
        "decision": (
            "SEMANTIC_LIFECYCLE_SIGNAL_CAN_REDUCE_HOSTED_PHYSICAL_RESIDENT_FOOTPRINT_WHEN_IT_CLOSES_REAL_MAPPINGS"
        ),
        "evidence_boundary": (
            "The lifecycle gate is synthetic. The mmap allocation, page faults, "
            "close operations, and process RSS observations are physical on the "
            "hosted Linux runner."
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_ANONYMOUS_MMAP_RESIDENCY_LIFECYCLE_ONLY"
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
