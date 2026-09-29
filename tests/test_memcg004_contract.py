from pathlib import Path
import json, unittest
from finite_ram_lab.memcg004_calibrated_stock import load_spec
ROOT=Path(__file__).resolve().parents[1]
class Contract(unittest.TestCase):
 def test_worker_is_zero_touch_protocol(self):
  s=(ROOT/"experiments/memcg004_worker.c").read_text()
  self.assertIn("int touched = 0;",s); self.assertIn('"TOUCH_ONE"',s); self.assertNotIn("touch_page(region, page_size, 0);",s)
 def test_workflow_launch_is_explicit(self):
  s=(ROOT/".github/workflows/memcg-004-calibrated-stock.yml").read_text()
  self.assertIn("launch/MEMCG-004-v1.txt",s); self.assertIn("ubuntu-26.04",s)
 def test_frozen_spec_shape(self):
  s=load_spec(ROOT/"specs/MEMCG-004-CALIBRATED-STOCK-v1.json")
  self.assertEqual(s["arms"],["calibrated","no_hold","control_no_prime"]); self.assertEqual(s["predicted_r"],64)
if __name__=="__main__":unittest.main()
