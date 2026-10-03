from __future__ import annotations

import unittest

from finite_ram_lab.fr_transfer_staging import (
    _parse_kib,
)


class FrTransferStagingTests(
    unittest.TestCase
):
    def test_parse_kib(self):
        row = _parse_kib(
            "Pss: 123 kB\n"
            "Rss: 456 kB\n"
        )

        self.assertEqual(
            row["Pss"],
            123,
        )

        self.assertEqual(
            row["Rss"],
            456,
        )


if __name__ == "__main__":
    unittest.main()
