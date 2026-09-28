from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.memcg002_cpu_stock import (
    analyze_trial,
    circular_distance,
    schedule_rows,
    write_schedule,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "specs/MEMCG-002-CPU-STOCK-CAUSAL-v1.json")
    .read_text(encoding="utf-8")
)


def synthetic_rows(arm: str, cpu_a: int = 0, cpu_b: int = 1) -> list[dict]:
    # A phase = 34. B cold-stock intervention charges immediately at 129.
    events = {}
    if arm == "fixed_touch":
        events = {34: 64, 98: 64, 162: 64, 226: 64}
    elif arm == "migrate_touch":
        events = {34: 64, 98: 64, 129: 64, 193: 64}
    elif arm == "roundtrip_touch":
        events = {34: 64, 98: 64, 129: 64, 226: 64}
    elif arm == "roundtrip_control":
        events = {}

    cur_pages = 0
    rows = []
    for step in range(257):
        if step in events:
            cur_pages += events[step]

        cpu = cpu_a
        if arm in {"migrate_touch", "roundtrip_touch", "roundtrip_control"}:
            if step > 128:
                cpu = cpu_b
            if arm in {"roundtrip_touch", "roundtrip_control"} and step > 192:
                cpu = cpu_a

        rows.append({
            "arm": arm,
            "step": step,
            "cpu_a": cpu_a,
            "cpu_b": cpu_b,
            "current_cpu": cpu,
            "page_size": 4096,
            "migration_marker": 1 if step == 129 else 2 if step == 193 else 0,
            "touched": 0 if arm == "roundtrip_control" else int(step > 0),
            "memory_current_bytes": 1000000 + cur_pages * 4096,
            "anon_bytes": 0,
            "kernel_bytes": 0,
            "pagetables_bytes": 0,
            "minor_faults": step,
        })
    return rows


class Memcg002Tests(unittest.TestCase):
    def test_schedule_complete_and_deterministic(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual({r["arm"] for r in rows}, set(SPEC["arms"]))
        self.assertEqual(rows, schedule_rows(SPEC, 0))

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 5)

    def test_circular_distance(self) -> None:
        self.assertEqual(circular_distance(63, 0, 64), 1)
        self.assertEqual(circular_distance(34, 34, 64), 0)

    def test_fixed_touch_passes(self) -> None:
        r = analyze_trial(SPEC, synthetic_rows("fixed_touch"), block=0)
        self.assertTrue(r["arm_pass"])
        self.assertEqual(r["fixed_phase_error"], 0)

    def test_migrate_touch_passes(self) -> None:
        r = analyze_trial(SPEC, synthetic_rows("migrate_touch"), block=0)
        self.assertTrue(r["arm_pass"])
        self.assertEqual(r["migration_first_charge_delay"], 1)
        self.assertEqual(r["b_side_spacings"], [64])

    def test_roundtrip_restores_a_phase(self) -> None:
        r = analyze_trial(SPEC, synthetic_rows("roundtrip_touch"), block=0)
        self.assertTrue(r["arm_pass"])
        self.assertEqual(r["predicted_return_step"], 226)
        self.assertEqual(r["observed_return_step"], 226)
        self.assertEqual(r["return_phase_error"], 0)

    def test_control_has_no_events(self) -> None:
        r = analyze_trial(SPEC, synthetic_rows("roundtrip_control"), block=0)
        self.assertTrue(r["arm_pass"])
        self.assertEqual(r["positive_events"], [])

    def test_worker_compiles_when_gcc_available(self) -> None:
        gcc = shutil.which("gcc")
        if not gcc:
            self.skipTest("gcc unavailable")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "worker"
            subprocess.run(
                [
                    gcc, "-O2", "-Wall", "-Wextra", "-std=c11",
                    "-D_GNU_SOURCE",
                    str(ROOT / "experiments/memcg002_worker.c"),
                    "-o", str(out),
                ],
                check=True,
            )
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
