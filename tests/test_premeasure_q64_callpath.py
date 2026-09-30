from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.premeasure_q64_callpath import (
    aggregate,
    bind_q64_probe_to_pid,
    close_q64_probe,
    parse_q64_stacks,
)


class PremeasureQ64CallpathTests(unittest.TestCase):
    def test_parse_target_q64_stack(self) -> None:
        trace = """
x-1 [000] ... 10.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=90 PRE
frltx405-222 [007] ... 10.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frltx405"
 => page_counter_try_charge
 => try_charge_memcg
 => mem_cgroup_charge_skmem
x-1 [000] ... 10.000000020: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=90 POST
"""
        rows = parse_q64_stacks(
            trace,
            trial_id="0:0",
            phase="OBSERVE",
            touch_number=90,
            target_pid=222,
            stock_cpu=7,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["frames"][:3],
            [
                "page_counter_try_charge",
                "try_charge_memcg",
                "mem_cgroup_charge_skmem",
            ],
        )

    def test_stack_parser_ignores_other_pid_and_cpu(self) -> None:
        trace = """
x-1 [000] ... 11.000000000: tracing_mark_write: FRL_TX trial=1:2 epoch=0 phase=OBSERVE touch=90 PRE
other-111 [007] ... 11.000000010: frl_pc_try64: counter=0xaaa nr_pages=64 comm="other"
 => page_counter_try_charge
frltx405-222 [006] ... 11.000000020: frl_pc_try64: counter=0xbbb nr_pages=64 comm="frltx405"
 => page_counter_try_charge
x-1 [000] ... 11.000000030: tracing_mark_write: FRL_TX trial=1:2 epoch=0 phase=OBSERVE touch=90 POST
"""
        rows = parse_q64_stacks(
            trace,
            trial_id="1:2",
            phase="OBSERVE",
            touch_number=90,
            target_pid=222,
            stock_cpu=7,
        )
        self.assertEqual(rows, [])

    def test_probe_lifecycle_binds_pid_and_stacktrace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "trace"
            probe = Path(td) / "events" / "kprobes" / "frl_pc_try64"
            probe.mkdir(parents=True)
            for name in ["enable", "filter", "trigger"]:
                (probe / name).write_text("", encoding="utf-8")

            bind_q64_probe_to_pid(trace, 222)
            self.assertEqual(
                (probe / "filter").read_text(encoding="utf-8"),
                "nr_pages == 64 && common_pid == 222\n",
            )
            self.assertEqual(
                (probe / "trigger").read_text(encoding="utf-8"),
                "stacktrace if common_pid == 222\n",
            )
            self.assertEqual(
                (probe / "enable").read_text(encoding="utf-8"),
                "1\n",
            )

            close_q64_probe(trace)
            self.assertEqual(
                (probe / "filter").read_text(encoding="utf-8"),
                "nr_pages == 64 && common_pid == 0\n",
            )
            self.assertEqual(
                (probe / "enable").read_text(encoding="utf-8"),
                "0\n",
            )

    def test_aggregate_passes_complete_synthetic_panel(self) -> None:
        spec = {
            "experiment_id": "TX-PREMEASURE-Q64-CALLPATH-v1",
            "design": {"total_identities": 4, "settle_arms_ms": [0, 5]},
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(2):
                b = root / f"block-{block}"
                b.mkdir()
                (b / "kprobe-profile.txt").write_text(
                    "frl_pc_try64 20 0\n",
                    encoding="utf-8",
                )
                for identity in range(2):
                    pre = (
                        [
                            {
                                "frames": [
                                    "page_counter_try_charge",
                                    "try_charge_memcg",
                                ]
                            }
                        ]
                        if identity == 1
                        else []
                    )
                    row = {
                        "classification": "WITHIN_BOUND",
                        "settle_ms": 5 if identity == 1 else 0,
                        "premeasurement_q64_count": len(pre),
                        "premeasurement_q64": pre,
                        "premeasurement_stack_receipt_complete": True,
                        "first_q64_touch": 1 if identity == 0 else 40,
                        "pid": 1000 + block * 10 + identity,
                        "cgroup_procs": [1000 + block * 10 + identity],
                    }
                    (b / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(row),
                        encoding="utf-8",
                    )

            result = aggregate(spec, root)

        self.assertTrue(result["experiment_pass"])
        self.assertTrue(result["coverage_pass"])
        self.assertTrue(result["stack_receipt_complete"])
        self.assertTrue(result["single_process_all"])
        self.assertEqual(result["premeasurement_q64_event_count"], 2)
        self.assertIn(
            "page_counter_try_charge > try_charge_memcg",
            result["callpath_fingerprints"],
        )


if __name__ == "__main__":
    unittest.main()
