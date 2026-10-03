from __future__ import annotations

import unittest

from finite_ram_lab.fr_compressibility_surface import (
    _compress,
    _decompress,
    _payload,
)


class FrCompressibilitySurfaceTests(
    unittest.TestCase
):
    def test_payloads_have_expected_size(self):
        for name in (
            "ZERO",
            "REPEATED_BLOCK",
            "SPARSE_OUTLIER",
            "LOW_ENTROPY_4BIT",
            "RANDOM",
        ):
            payload = _payload(
                name,
                size_bytes=1024 * 1024,
                repetition=0,
            )

            self.assertEqual(
                len(payload),
                1024 * 1024,
            )

    def test_codecs_roundtrip(self):
        payload = _payload(
            "LOW_ENTROPY_4BIT",
            size_bytes=256 * 1024,
            repetition=0,
        )

        for codec in (
            "ZLIB_1",
            "ZLIB_9",
            "BZ2_1",
            "LZMA_0",
        ):
            compressed = _compress(
                codec,
                payload,
            )

            restored = _decompress(
                codec,
                compressed,
            )

            self.assertEqual(
                restored,
                payload,
            )


if __name__ == "__main__":
    unittest.main()
