from __future__ import annotations
import unittest
from finite_ram_lab.template_projection import pct
class TemplateProjectionTests(unittest.TestCase):
    def test_pct(self): self.assertEqual(pct([1,2,3,4,5],.95),4.0)
if __name__=='__main__': unittest.main()
