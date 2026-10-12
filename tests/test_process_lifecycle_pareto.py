from __future__ import annotations
import unittest
from finite_ram_lab.process_lifecycle_pareto import percentile
class ProcessParetoTests(unittest.TestCase):
    def test_percentile(self): self.assertEqual(percentile([1,2,3,4,5],.95),4.0)
if __name__=='__main__': unittest.main()
