from __future__ import annotations

import unittest

from finite_ram_lab.obs006_charge_side_q64 import classify_trial, parse_trace


class OBS006Tests(unittest.TestCase):
    def _trial(self) -> dict:
        def row(touch: int, delta: float = 0.0) -> dict:
            return {
                "touch_number": touch,
                "delta_pages": delta,
                "vmpte_delta_kib": 0,
            }

        return {
            "block": 0,
            "identity": 0,
            "primer_touch": 2,
            "scrub_flush_touch": 5,
            "discard": {"worker_error": 0},
            "collision_pages": 14,
            "calibration": [row(1), row(2, 64.0)],
            "consume": [row(i) for i in range(1, 34)],
            "producer": [row(i) for i in range(1, 18)],
            "collision": [row(i, 47.0 if i == 14 else 0.0) for i in range(1, 15)],
        }

    def test_masked_q64_direct_chain(self) -> None:
        text = """
x-1 [000] ...: tracing_mark_write: FRL_OBS006 trial=0:0 phase=COLLISION touch=14 PRE
frlq6-10 [003] ...: frl_pc_try64: counter=0xaaa nr_pages=64 comm="frlq6"
frlq6-10 [003] ...: frl_refill_stock: memcg=0xbbb nr_pages=63 comm="frlq6"
frlq6-10 [003] ...: frl_lru_flush: nr=31 comm="frlq6"
frlq6-10 [003] ...: frl_folios_put: nr=31 comm="frlq6"
frlq6-10 [003] ...: frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm="frlq6"
x-1 [000] ...: tracing_mark_write: FRL_OBS006 trial=0:0 phase=COLLISION touch=14 POST
"""
        result = classify_trial(self._trial(), parse_trace(text))
        self.assertEqual(result["classification"], "MASKED_Q64_PASS")
        self.assertTrue(result["final_direct_q64"])
        self.assertTrue(result["final_direct_release17"])
        self.assertTrue(result["final_lru_flush31"])
        self.assertTrue(result["final_net47"])

    def test_early_release_fails_closed(self) -> None:
        text = """
x-1 [000] ...: tracing_mark_write: FRL_OBS006 trial=0:0 phase=COLLISION touch=9 PRE
other-20 [003] ...: frl_pc_uncharge17: counter=0xaaa nr_pages=17 comm="other"
x-1 [000] ...: tracing_mark_write: FRL_OBS006 trial=0:0 phase=COLLISION touch=9 POST
"""
        result = classify_trial(self._trial(), parse_trace(text))
        self.assertEqual(result["classification"], "EARLY_RELEASE")


if __name__ == "__main__":
    unittest.main()
