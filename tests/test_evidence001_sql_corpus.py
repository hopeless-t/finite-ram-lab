from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.evidence001_sql_corpus import build_db, run_discovery


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "evidence/EVIDENCE-001/seed-v1.json"
SCHEMA = ROOT / "sql/evidence001_schema.sql"


class Evidence001Tests(unittest.TestCase):
    def build(self, td: str) -> Path:
        db = Path(td) / "corpus.sqlite"
        build_db(SEED, SCHEMA, db)
        return db

    def test_build_and_semantic_views(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = self.build(td)
            con = sqlite3.connect(db)
            try:
                self.assertEqual(
                    con.execute("SELECT COUNT(*) FROM experiments").fetchone()[0],
                    8,
                )
                self.assertEqual(
                    con.execute(
                        "SELECT COUNT(*) FROM v_clean_floor "
                        "WHERE floor_semantics!='clean_pre_observer'"
                    ).fetchone()[0],
                    0,
                )
                self.assertGreater(
                    con.execute("SELECT COUNT(*) FROM v_legacy_floor").fetchone()[0],
                    0,
                )
            finally:
                con.close()

    def test_discovery_recovers_known_relations(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = self.build(td)
            result = run_discovery(db)

        self.assertTrue(
            result["pressure_fixed_raw_knee"]["intersection_empty"]
        )
        self.assertEqual(
            result["live_set_transformed_interval"]["max_lower_exclusive_mib"],
            144,
        )
        self.assertEqual(
            result["live_set_transformed_interval"]["min_upper_inclusive_mib"],
            152,
        )
        self.assertTrue(
            result["capacity_knee"]["invariant_at_current_resolution"]
        )
        self.assertAlmostEqual(
            result["clean_floor"]["span_mib"],
            0.248046875,
        )

    def test_seed_has_no_unknown_floor_semantics(self) -> None:
        data = json.loads(SEED.read_text(encoding="utf-8"))
        allowed = {
            "clean_pre_observer",
            "legacy_post_observer",
            "post_observer_diagnostic",
            "not_applicable",
        }
        self.assertTrue(
            all(row["floor_semantics"] in allowed for row in data["response_cells"])
        )


if __name__ == "__main__":
    unittest.main()
