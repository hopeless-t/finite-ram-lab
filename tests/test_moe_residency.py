import unittest

from finite_ram_lab.moe_residency import (
    MoEGeometry,
    evaluate,
    panel,
    uniform_expected_distinct_experts,
)


class TestMoEResidency(unittest.TestCase):
    def test_published_active_parameter_count_is_rederived_exactly(self):
        g = MoEGeometry()
        g.validate()
        self.assertEqual(g.expert_params, 7_372_800)
        self.assertEqual(g.all_expert_params, 30_198_988_800)
        self.assertEqual(g.derived_active_params, 3_827_476_992)

    def test_uniform_union_expands_toward_all_experts(self):
        g = MoEGeometry()
        self.assertEqual(uniform_expected_distinct_experts(1, g), 8.0)
        self.assertGreater(uniform_expected_distinct_experts(16, g), 80.0)
        self.assertGreater(uniform_expected_distinct_experts(64, g), 125.0)
        self.assertLessEqual(
            uniform_expected_distinct_experts(256, g), g.experts_per_layer
        )

    def test_more_cache_trades_ram_for_less_streaming(self):
        a = evaluate(8, 0.75, 2500.0)
        b = evaluate(16, 0.75, 2500.0)
        self.assertGreater(
            b["resident_mib_bf16_plus_reserve"],
            a["resident_mib_bf16_plus_reserve"],
        )
        self.assertLess(
            b["stream_mib_per_token_bf16"],
            a["stream_mib_per_token_bf16"],
        )

    def test_routing_skew_improves_static_hotset_hit_mass(self):
        uniform = evaluate(16, 0.0, 2500.0)
        skewed = evaluate(16, 1.25, 2500.0)
        self.assertGreater(skewed["hotset_hit_mass"], uniform["hotset_hit_mass"])
        self.assertLess(
            skewed["stream_mib_per_token_bf16"],
            uniform["stream_mib_per_token_bf16"],
        )

    def test_sixteen_slot_shadow_window_is_below_sixteen_gib(self):
        row = evaluate(16, 0.75, 2500.0)
        self.assertLess(row["resident_gib_bf16_plus_reserve"], 16.0)

    def test_full_expert_cache_has_zero_streaming(self):
        row = evaluate(128, 0.0, 2500.0)
        self.assertEqual(row["stream_mib_per_token_bf16"], 0.0)
        self.assertIsNone(row["io_bound_tokens_per_s"])

    def test_panel_shape_and_claim_ceiling(self):
        result = panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["claim_ceiling"],
            "ANALYTIC_ROUTING_RESIDENCY_SHADOW_MODEL_ONLY",
        )
        self.assertEqual(len(result["rows"]), 36)


if __name__ == "__main__":
    unittest.main()
