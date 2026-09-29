from __future__ import annotations

import unittest

from finite_ram_lab.obs005_cross_cgroup_lru import classify_trial, parse_trace


class OBS005Tests(unittest.TestCase):
    def test_controlled_handoff(self) -> None:
        text = """
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 START
frlprod-10 [003] ...: frl_pc_try: counter=0xaaa nr_pages=64 comm="frlprod"
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 phase=TRIGGER touch=14 PRE
frltrig-11 [003] ...: frl_lru_flush: nr=31 comm="frltrig"
frltrig-11 [003] ...: frl_folios_put: nr=31 comm="frltrig"
frltrig-11 [003] ...: frl_pc_uncharge: counter=0xaaa nr_pages=17 comm="frltrig"
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 phase=TRIGGER touch=14 POST
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 END
"""
        traces = parse_trace(text)
        trial = {
            "producer_pid": 10,
            "scrub_flush_touch": 7,
            "trigger_pages": 14,
        }
        result = classify_trial(trial, traces["0:0"])
        self.assertEqual(result["classification"], "CONTROLLED_HANDOFF_PASS")

    def test_producer_flush_is_contaminated(self) -> None:
        text = """
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 START
frlprod-10 [003] ...: frl_pc_try: counter=0xaaa nr_pages=64 comm="frlprod"
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 phase=PRODUCER touch=4 PRE
frlprod-10 [003] ...: frl_lru_flush: nr=31 comm="frlprod"
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 phase=PRODUCER touch=4 POST
x-1 [000] ...: tracing_mark_write: FRL_OBS005 trial=0:0 END
"""
        result = classify_trial(
            {"producer_pid": 10, "scrub_flush_touch": 2, "trigger_pages": 14},
            parse_trace(text)["0:0"],
        )
        self.assertEqual(
            result["classification"],
            "PRODUCER_FLUSH_CONTAMINATED",
        )


if __name__ == "__main__":
    unittest.main()
