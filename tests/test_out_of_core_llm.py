import math
import unittest

from finite_ram_lab.out_of_core_llm import (
    ModelGeometry,
    OutOfCoreCase,
    evaluate,
    panel,
)


class OutOfCoreLlmTests(unittest.TestCase):
    def setUp(self):
        self.ptq = ModelGeometry("PTQ1", 5.95)

    def test_geometry_is_positive_and_has_64_blocks(self):
        self.assertEqual(self.ptq.block_count, 64)
        self.assertGreater(self.ptq.block_mib, 0)
        self.assertGreater(self.ptq.pinned_nonblock_mib, 0)

    def test_more_resident_budget_never_increases_streamed_blocks(self):
        low = evaluate(self.ptq, OutOfCoreCase(2048, 2500))
        high = evaluate(self.ptq, OutOfCoreCase(4096, 2500))
        self.assertLessEqual(high["streamed_blocks"], low["streamed_blocks"])
        self.assertLessEqual(
            high["decode_io_mib_per_token"],
            low["decode_io_mib_per_token"],
        )

    def test_more_bandwidth_improves_io_bound(self):
        slow = evaluate(self.ptq, OutOfCoreCase(2048, 1000))
        fast = evaluate(self.ptq, OutOfCoreCase(2048, 5000))
        self.assertGreater(fast["decode_io_bound_tps"], slow["decode_io_bound_tps"])

    def test_prefill_amortizes_weight_io(self):
        short = evaluate(
            self.ptq,
            OutOfCoreCase(2048, 2500, prefill_tokens=512),
        )
        long = evaluate(
            self.ptq,
            OutOfCoreCase(2048, 2500, prefill_tokens=4096),
        )
        self.assertLess(
            long["prefill_io_mib_per_token"],
            short["prefill_io_mib_per_token"],
        )

    def test_smaller_pack_has_no_worse_decode_io_at_same_budget(self):
        ptq = evaluate(ModelGeometry("PTQ1", 5.95), OutOfCoreCase(2048, 2500))
        pq2 = evaluate(ModelGeometry("PQ2", 7.21), OutOfCoreCase(2048, 2500))
        self.assertLessEqual(
            ptq["decode_io_mib_per_token"],
            pq2["decode_io_mib_per_token"],
        )

    def test_panel_contract(self):
        result = panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["claim_ceiling"],
            "ANALYTIC_OUT_OF_CORE_LLM_SHADOW_MODEL_ONLY",
        )
        self.assertEqual(len(result["rows"]), 24)


if __name__ == "__main__":
    unittest.main()
