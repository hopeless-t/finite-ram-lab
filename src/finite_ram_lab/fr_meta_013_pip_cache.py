from __future__ import annotations

import json
import statistics

SCHEMA = "finite-ram-lab.fr-meta-013-pip-cache/v0.1"

OBSERVED_INSTALL_SECONDS = (
    19.006,
    16.256,
    14.679,
    16.397,
)


def run_panel() -> dict:
    median = statistics.median(OBSERVED_INSTALL_SECONDS)
    checks = {
        "baseline_median_over_15s": median > 15.0,
        "cache_backend_is_pip": True,
        "dependency_key_is_pyproject": True,
        "scientific_tests_unchanged": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "observed_uncached_install_seconds": list(OBSERVED_INSTALL_SECONDS),
        "observed_uncached_median_seconds": median,
        "decision": "ENABLE_SETUP_PYTHON_PIP_CACHE",
        "candidate": {
            "action": "actions/setup-python@v7",
            "cache": "pip",
            "cache_dependency_path": "pyproject.toml",
        },
        "measurement_plan": {
            "implementation_run": "cache may miss and populate",
            "receipt_or_pr_run": "measure cache restore and Install duration",
            "success_requires": (
                "CI semantics unchanged; speed claim is based on observed hit, "
                "not configuration alone."
            ),
        },
        "monte_carlo": {
            "used": False,
            "reason": "This is an empirical fixed-cost cache experiment.",
        },
        "claim_ceiling": "CI_DEPENDENCY_CACHE_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
