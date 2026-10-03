from __future__ import annotations

import json
import statistics

SCHEMA = "finite-ram-lab.fr-meta-013-pip-cache/v0.2"

OBSERVED_UNCACHED_SECONDS = (19.006, 16.256, 14.679, 16.397, 20.188)
PR_RETRY_SECONDS = 19.040


def run_panel() -> dict:
    baseline_median = statistics.median(OBSERVED_UNCACHED_SECONDS)
    speedup = baseline_median / PR_RETRY_SECONDS
    checks = {
        "implementation_cache_miss_observed": True,
        "pr_cache_miss_observed": True,
        "same_key_reused": True,
        "speedup_not_material": speedup < 1.10,
        "cache_save_overhead_observed": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "observed_uncached_install_seconds": list(OBSERVED_UNCACHED_SECONDS),
        "baseline_median_seconds": baseline_median,
        "pr_install_seconds": PR_RETRY_SECONDS,
        "measured_speedup_ratio": speedup,
        "cache_key": (
            "setup-python-Linux-x64-24.04-Ubuntu-python-3.12.14-pip-"
            "0297d4812f34fab52178c1cb36ba6dae036262df89c4b33cd7779c5cc05da388"
        ),
        "decision": "DO_NOT_PROMOTE_PIP_CACHE_FOR_CURRENT_STACKED_PR_FLOW",
        "theory_update": (
            "A configured cache is not a speed primitive until the exact "
            "workflow/ref topology demonstrates restore reuse. In this dogfood "
            "both implementation and PR runs missed the same key, while cache "
            "save added end-of-job work."
        ),
        "next": (
            "Revisit only with a cache topology whose scope is proven reusable, "
            "or move dependency preparation to a durable shared artifact/image."
        ),
        "claim_ceiling": "NEGATIVE_CI_DEPENDENCY_CACHE_RESULT_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
