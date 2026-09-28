from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ALLOWED_FLOOR_SEMANTICS = {
    "clean_pre_observer",
    "legacy_post_observer",
    "post_observer_diagnostic",
    "not_applicable",
}


def load_seed(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if int(data["version"]) != 1:
        raise ValueError("unsupported seed version")
    for row in data["response_cells"]:
        if row["floor_semantics"] not in ALLOWED_FLOOR_SEMANTICS:
            raise ValueError("unknown floor semantics")
    return data


def build_db(seed_path: str | Path, schema_path: str | Path, db_path: str | Path) -> None:
    data = load_seed(seed_path)
    out = Path(db_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    con = sqlite3.connect(out)
    try:
        con.executescript(Path(schema_path).read_text(encoding="utf-8"))
        con.executemany(
            """INSERT INTO experiments VALUES
            (:experiment_id,:run_id,:result_doc,:status,:runner,:artifact_digest,
             :accepted_at_bounce,:inference_boundary)""",
            data["experiments"],
        )
        cols = [
            "experiment_id","condition_id","runner","memory_high_mib",
            "memory_max_mib","hot_anon_mib","cold_file_mib",
            "release_interval_mib","arm_kind","median_high_events",
            "positive_trials","trial_count","median_peak_mib",
            "median_floor_mib","floor_scope","floor_semantics",
            "median_file_residency","advice_calls","oom_any",
        ]
        con.executemany(
            f"INSERT INTO response_cells ({','.join(cols)}) VALUES ({','.join(':'+c for c in cols)})",
            data["response_cells"],
        )
        cols = [
            "experiment_id","condition_id","memory_high_mib","hot_anon_mib",
            "cold_file_mib","knee_lower_exclusive_mib",
            "knee_upper_inclusive_mib","right_censored",
            "transformed_lower_exclusive_mib",
            "transformed_upper_inclusive_mib",
        ]
        con.executemany(
            f"INSERT INTO onset_intervals ({','.join(cols)}) VALUES ({','.join(':'+c for c in cols)})",
            data["onset_intervals"],
        )
        cols = [
            "experiment_id","condition_id","target_size_mib",
            "median_observer_delta_mib","positive_trials","trial_count",
            "retained_delta_mib","measurement",
        ]
        con.executemany(
            f"INSERT INTO observer_cells ({','.join(cols)}) VALUES ({','.join(':'+c for c in cols)})",
            data["observer_cells"],
        )
        con.executemany(
            "INSERT INTO measurement_notes VALUES (:note_id,:experiment_id,:kind,:text)",
            data["measurement_notes"],
        )
        con.commit()
        con.execute("PRAGMA integrity_check").fetchone()
    finally:
        con.close()


def scalar(con: sqlite3.Connection, sql: str) -> Any:
    row = con.execute(sql).fetchone()
    return None if row is None else row[0]


def run_discovery(db_path: str | Path) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        pressure = con.execute(
            """
            SELECT MAX(knee_lower_exclusive_mib) AS max_lower,
                   MIN(knee_upper_inclusive_mib) AS min_upper
            FROM onset_intervals
            WHERE experiment_id IN (
              'STRATA-004-KNEE-v1',
              'STRATA-005-EXTERNAL-VALIDITY-v1'
            )
            """
        ).fetchone()
        live = con.execute(
            """
            SELECT MAX(transformed_lower_exclusive_mib) AS max_lower,
                   MIN(transformed_upper_inclusive_mib) AS min_upper,
                   COUNT(*) AS n
            FROM v_live_set_transform
            """
        ).fetchone()
        capacity = con.execute(
            """
            SELECT COUNT(DISTINCT
              printf('%.6f/%.6f',knee_lower_exclusive_mib,knee_upper_inclusive_mib)
            ) AS distinct_brackets,
            COUNT(*) AS n,
            MIN(cold_file_mib) AS min_cold,
            MAX(cold_file_mib) AS max_cold
            FROM v_capacity_knee
            """
        ).fetchone()
        clean = con.execute(
            """
            SELECT MIN(median_floor_mib) AS min_floor,
                   MAX(median_floor_mib) AS max_floor,
                   MAX(median_floor_mib)-MIN(median_floor_mib) AS span,
                   COUNT(*) AS n
            FROM v_clean_floor
            WHERE experiment_id='REC-004-PREPOST-OBSERVER-HYGIENE-v1'
            """
        ).fetchone()
        obs = [
            dict(r) for r in con.execute(
                """
                SELECT experiment_id,target_size_mib,
                       median_observer_delta_mib,positive_trials,trial_count
                FROM v_observer_effect
                ORDER BY experiment_id,target_size_mib
                """
            )
        ]

        tested_axes = {
            "pressure": True,
            "hot_live_set": True,
            "runner_image": True,
            "cold_capacity": True,
            "observer_hygiene": True,
            "access_pattern": False,
            "concurrent_streams": False,
            "read_chunk_size": False,
            "write_path": False,
        }
        next_axes = [
            {"axis":"access_pattern","priority":1,"reason":"only sequential one-shot reads tested"},
            {"axis":"concurrent_streams","priority":2,"reason":"single-stream evidence only"},
            {"axis":"read_chunk_size","priority":3,"reason":"4 MiB chunk fixed across accepted studies"},
            {"axis":"write_path","priority":4,"reason":"read-side page-cache mechanism only"},
        ]

        return {
            "pressure_fixed_raw_knee": {
                "max_lower_exclusive_mib": pressure["max_lower"],
                "min_upper_inclusive_mib": pressure["min_upper"],
                "intersection_empty": pressure["max_lower"] >= pressure["min_upper"],
            },
            "live_set_transformed_interval": {
                "max_lower_exclusive_mib": live["max_lower"],
                "min_upper_inclusive_mib": live["min_upper"],
                "row_count": live["n"],
                "compatible": live["max_lower"] < live["min_upper"],
            },
            "capacity_knee": {
                "distinct_brackets": capacity["distinct_brackets"],
                "row_count": capacity["n"],
                "cold_range_mib": [capacity["min_cold"], capacity["max_cold"]],
                "invariant_at_current_resolution": capacity["distinct_brackets"] == 1,
            },
            "clean_floor": {
                "min_mib": clean["min_floor"],
                "max_mib": clean["max_floor"],
                "span_mib": clean["span"],
                "row_count": clean["n"],
            },
            "observer_effect": obs,
            "axis_coverage": tested_axes,
            "next_axis_ranking": next_axes,
        }
    finally:
        con.close()


def render_md(result: dict[str, Any]) -> str:
    p = result["pressure_fixed_raw_knee"]
    l = result["live_set_transformed_interval"]
    c = result["capacity_knee"]
    f = result["clean_floor"]
    lines = [
        "# EVIDENCE-001 SQL Discovery",
        "",
        f"- fixed raw knee intersection empty: **{p['intersection_empty']}**",
        f"- live-set transformed interval: **({l['max_lower_exclusive_mib']}, {l['min_upper_inclusive_mib']}] MiB**",
        f"- capacity knee invariant across {c['cold_range_mib'][0]}–{c['cold_range_mib'][1]} MiB: **{c['invariant_at_current_resolution']}**",
        f"- clean pre-observer floor span: **{f['span_mib']:.6f} MiB**",
        "",
        "## Next untested axes",
        "",
    ]
    for row in result["next_axis_ranking"]:
        lines.append(f"{row['priority']}. {row['axis']}: {row['reason']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--json-out", required=True)
    p.add_argument("--md-out", required=True)
    args = p.parse_args()

    build_db(args.seed, args.schema, args.db)
    result = run_discovery(args.db)

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mout.write_text(render_md(result), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
