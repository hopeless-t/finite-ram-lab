from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.fr_page_cache_residency import (
    _new_file,
    _resident_ratio,
    _map,
)


class FrPageCacheResidencyTests(
    unittest.TestCase
):
    def test_mincore_returns_fraction(self):
        with tempfile.TemporaryDirectory() as temp:
            path = (
                Path(temp)
                / "small.bin"
            )

            fd = _new_file(
                path,
                1024 * 1024,
            )

            try:
                mapping = _map(
                    fd,
                    1024 * 1024,
                )

                try:
                    row = (
                        _resident_ratio(
                            mapping
                        )
                    )

                    self.assertGreater(
                        row["pages"],
                        0,
                    )

                    self.assertGreaterEqual(
                        row[
                            "resident_fraction"
                        ],
                        0.0,
                    )

                    self.assertLessEqual(
                        row[
                            "resident_fraction"
                        ],
                        1.0,
                    )

                finally:
                    mapping.close()

            finally:
                import os
                os.close(
                    fd
                )


if __name__ == "__main__":
    unittest.main()
