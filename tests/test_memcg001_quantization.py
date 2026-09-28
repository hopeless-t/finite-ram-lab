from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.memcg001_quantization import (
    analyze_rows,
    schedule_rows,
    write_schedule,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "specs/MEMCG-001-PAGE-CHARGE-QUANTIZATION-v1.json")
    .read_text(encoding="utf-8")
)


def synthetic_rows(mode: str, *, q64: bool) -> list[dict]:
    rows = []
    current_pages = 0
    jumps = {10, 74, 138, 202} if q64 and mode == "touch" else set()
    for step in range(257):
        if step > 0:
            if step in jumps:
                current_pages += 64
            elif mode == "touch" and not q64:
                current_pages += 1
        rows.append({
            "mode": mode,
            "step": step,
            "pinned_cpu": 3,
            "page_size": 4096,
            "memory_current_bytes": 1000000 + current_pages * 4096,
            "anon_bytes": 0,
            "kernel_bytes": 0,
            "pagetables_bytes": 0,
            "minor_faults": step,
        })
    return rows


class Memcg001Tests(unittest.TestCase):
    def test_schedule_has_both_modes(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual({r["mode"] for r in rows}, {"touch", "control"})
        self.assertEqual(rows, schedule_rows(SPEC, 0))

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 3)

    def test_h64_synthetic_support(self) -> None:
        result = analyze_rows(
            SPEC, synthetic_rows("touch", q64=True), block=0
        )
        self.assertTrue(result.supports_h64)
        self.assertEqual(result.median_significant_jump_pages, 64)
        self.assertEqual(result.median_spacing_pages, 64)
        self.assertEqual(result.best_quantum_pages, 64)

    def test_page_linear_rejects_h64(self) -> None:
        result = analyze_rows(
            SPEC, synthetic_rows("touch", q64=False), block=0
        )
        self.assertFalse(result.supports_h64)
        self.assertEqual(result.significant_jump_pages, [])

    def test_control_has_no_h64(self) -> None:
        result = analyze_rows(
            SPEC, synthetic_rows("control", q64=False), block=0
        )
        self.assertFalse(result.supports_h64)

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
                    str(ROOT / "experiments/memcg001_worker.c"),
                    "-o", str(out),
                ],
                check=True,
            )
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
