from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.fr_duplication_tax import (
    _parse_kib,
    _write_backing,
)


class FrDuplicationTaxTests(
    unittest.TestCase
):
    def test_parse_kib(self):
        row = _parse_kib(
            "Rss: 100 kB\n"
            "Pss: 75 kB\n"
        )

        self.assertEqual(
            row["Rss"],
            100,
        )
        self.assertEqual(
            row["Pss"],
            75,
        )

    def test_backing_file_size(self):
        with tempfile.TemporaryDirectory() as temp:
            path = (
                Path(temp)
                / "x.bin"
            )

            _write_backing(
                path,
                2 * 1024 * 1024,
            )

            self.assertEqual(
                path.stat().st_size,
                2 * 1024 * 1024,
            )


if __name__ == "__main__":
    unittest.main()
