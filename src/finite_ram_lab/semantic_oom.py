from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations
import json


SCHEMA = "finite-ram-lab.semantic-oom/v0.1"
PRESSURE_DEFICITS_MIB = (1024, 2048, 3072, 4096, 5120)


@dataclass(frozen=True)
class ProcessFixture:
    name: str
    rss_mib: int
    oom_score: int
    task_value: int
    reconstruction_cost: int
    unsaved_state: int
    current_task: bool = False
    hard_protected: bool = False

    @property
    def semantic_loss(self) -> int:
        return (
            self.task_value
            + self.reconstruction_cost
            + 100 * self.unsaved_state
        )


def corpus() -> tuple[ProcessFixture, ...]:
    return (
        ProcessFixture(
            name="desktop-shell",
            rss_mib=350,
            oom_score=100,
            task_value=100,
            reconstruction_cost=100,
            unsaved_state=0,
            current_task=True,
            hard_protected=True,
        ),
        ProcessFixture(
            name="chrome-active",
            rss_mib=3200,
            oom_score=950,
            task_value=100,
            reconstruction_cost=80,
            unsaved_state=1,
            current_task=True,
        ),
        ProcessFixture(
            name="terminal-session",
            rss_mib=500,
            oom_score=250,
            task_value=85,
            reconstruction_cost=60,
            unsaved_state=1,
            current_task=True,
        ),
        ProcessFixture(
            name="model-worker",
            rss_mib=2500,
            oom_score=820,
            task_value=35,
            reconstruction_cost=20,
            unsaved_state=0,
        ),
        ProcessFixture(
            name="batch-compressor",
            rss_mib=2200,
            oom_score=700,
            task_value=8,
            reconstruction_cost=5,
            unsaved_state=0,
        ),
        ProcessFixture(
            name="background-indexer",
            rss_mib=1600,
            oom_score=650,
            task_value=3,
            reconstruction_cost=2,
            unsaved_state=0,
        ),
    )


def _eligible() -> tuple[ProcessFixture, ...]:
    return tuple(
        process
        for process in corpus()
        if not process.hard_protected
    )


def _decision(
    *,
    policy: str,
    selected: tuple[ProcessFixture, ...],
    deficit_mib: int,
) -> dict:
    freed = sum(process.rss_mib for process in selected)
    loss = sum(process.semantic_loss for process in selected)
    current_task_killed = any(
        process.current_task for process in selected
    )
    return {
        "policy": policy,
        "pressure_deficit_mib": deficit_mib,
        "victims": [process.name for process in selected],
        "freed_mib": freed,
        "relief_satisfied": freed >= deficit_mib,
        "excess_relief_mib": max(0, freed - deficit_mib),
        "semantic_loss": loss,
        "current_task_survives": not current_task_killed,
        "victim_count": len(selected),
    }


def earlyoom_like_oom_score(deficit_mib: int) -> dict:
    """Static-snapshot approximation of default oom_score victim ordering.

    This is not an implementation of earlyoom. It intentionally models only
    the documented default victim ranking dimension: highest oom_score first.
    """
    ranked = sorted(
        _eligible(),
        key=lambda process: (
            process.oom_score,
            process.rss_mib,
            process.name,
        ),
        reverse=True,
    )

    selected: list[ProcessFixture] = []
    freed = 0
    for process in ranked:
        if freed >= deficit_mib:
            break
        selected.append(process)
        freed += process.rss_mib

    return _decision(
        policy="EARLYOOM_LIKE_OOM_SCORE",
        selected=tuple(selected),
        deficit_mib=deficit_mib,
    )


def rss_first(deficit_mib: int) -> dict:
    ranked = sorted(
        _eligible(),
        key=lambda process: (
            process.rss_mib,
            process.oom_score,
            process.name,
        ),
        reverse=True,
    )

    selected: list[ProcessFixture] = []
    freed = 0
    for process in ranked:
        if freed >= deficit_mib:
            break
        selected.append(process)
        freed += process.rss_mib

    return _decision(
        policy="RSS_FIRST",
        selected=tuple(selected),
        deficit_mib=deficit_mib,
    )


def semantic_min_loss(deficit_mib: int) -> dict:
    """Exact small-corpus optimization for semantic loss under relief target."""
    eligible = _eligible()
    candidates: list[tuple[tuple[int, int, int, tuple[str, ...]], tuple[ProcessFixture, ...]]] = []

    for count in range(1, len(eligible) + 1):
        for subset in combinations(eligible, count):
            freed = sum(process.rss_mib for process in subset)
            if freed < deficit_mib:
                continue

            loss = sum(process.semantic_loss for process in subset)
            current_task_kills = sum(
                process.current_task for process in subset
            )
            excess = freed - deficit_mib
            names = tuple(sorted(process.name for process in subset))

            objective = (
                current_task_kills,
                loss,
                excess,
                names,
            )
            candidates.append((objective, subset))

    if not candidates:
        selected = eligible
    else:
        selected = min(candidates, key=lambda item: item[0])[1]

    return _decision(
        policy="SEMANTIC_MIN_LOSS",
        selected=tuple(selected),
        deficit_mib=deficit_mib,
    )


def run_panel() -> dict:
    rows: list[dict] = []

    for deficit in PRESSURE_DEFICITS_MIB:
        rows.extend(
            (
                earlyoom_like_oom_score(deficit),
                rss_first(deficit),
                semantic_min_loss(deficit),
            )
        )

    by_deficit: dict[str, dict[str, dict]] = {}
    for deficit in PRESSURE_DEFICITS_MIB:
        by_deficit[str(deficit)] = {
            row["policy"]: row
            for row in rows
            if row["pressure_deficit_mib"] == deficit
        }

    for deficit, policies in by_deficit.items():
        if not all(
            row["relief_satisfied"]
            for row in policies.values()
        ):
            raise RuntimeError(
                f"relief_not_satisfied:{deficit}"
            )

    semantic_improvement: dict[str, int] = {}
    for deficit in PRESSURE_DEFICITS_MIB:
        policies = by_deficit[str(deficit)]
        baseline = policies["EARLYOOM_LIKE_OOM_SCORE"]
        semantic = policies["SEMANTIC_MIN_LOSS"]
        semantic_improvement[str(deficit)] = (
            baseline["semantic_loss"]
            - semantic["semantic_loss"]
        )

    protected_deficits = [
        deficit
        for deficit in PRESSURE_DEFICITS_MIB
        if by_deficit[str(deficit)][
            "SEMANTIC_MIN_LOSS"
        ]["current_task_survives"]
    ]

    if by_deficit["1024"][
        "EARLYOOM_LIKE_OOM_SCORE"
    ]["victims"] != ["chrome-active"]:
        raise RuntimeError(
            "baseline_counterexample_not_frozen"
        )

    if not all(
        semantic_improvement[str(deficit)] > 0
        for deficit in (1024, 2048, 3072, 4096, 5120)
    ):
        raise RuntimeError(
            "semantic_policy_not_improved"
        )

    if protected_deficits != [1024, 2048, 3072]:
        raise RuntimeError(
            "semantic_task_survival_boundary_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_SEMANTIC_OOM_COUNTEREXAMPLE_VALIDATED"
        ),
        "synthetic_only": True,
        "empirical_earlyoom_claim": False,
        "processes": [
            {
                **asdict(process),
                "semantic_loss": process.semantic_loss,
            }
            for process in corpus()
        ],
        "pressure_deficits_mib": list(
            PRESSURE_DEFICITS_MIB
        ),
        "rows": rows,
        "semantic_loss_improvement_vs_oom_score": (
            semantic_improvement
        ),
        "semantic_current_task_survival_deficits_mib": (
            protected_deficits
        ),
        "claim_ceiling": (
            "SYNTHETIC_VICTIM_SELECTION_COUNTEREXAMPLE_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
