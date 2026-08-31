import unittest
import os
from zero_shrink import ZeroShrinkEngine, HuffmanCoder, Transforms

class TestZeroShrink(unittest.TestCase):
    def setUp(self):
        self.engine = ZeroShrinkEngine()
        self.test_data = b"Hello World! This is a test of the ZeroShrink adaptive compression engine. Hello World!"

    def test_roundtrip(self):
        compressed = self.engine.compress(self.test_data)
        decompressed = self.engine.decompress(compressed)
        self.assertEqual(self.test_data, decompressed)

    def test_empty_file(self):
        data = b""
        compressed = self.engine.compress(data)
        decompressed = self.engine.decompress(compressed)
        self.assertEqual(data, decompressed)

    def test_repetitive_data(self):
        data = b"AAAAA" * 100
        compressed = self.engine.compress(data)
        decompressed = self.engine.decompress(compressed)
        self.assertEqual(data, decompressed)

    def test_single_symbol_data(self):
        data = b"Z" * 10000
        compressed = self.engine.compress(data)
        decompressed = self.engine.decompress(compressed)
        self.assertEqual(data, decompressed)

    def test_huffman_coder_direct(self):
        coder = HuffmanCoder()
        data = b"The quick brown fox jumps over the lazy dog" * 50
        payload, mapping, padding = coder.compress(data)
        decompressed = coder.decompress(payload, mapping, padding)
        self.assertEqual(data, decompressed)

    def test_large_file(self):
        # 1 MB dataset with varied patterns
        data = os.urandom(10000) * 100
        compressed, codec_type = self.engine.compress(data, return_type=True)
        self.assertTrue(len(compressed) > 0)
        decompressed = self.engine.decompress(compressed)
        self.assertEqual(data, decompressed)

    def test_corrupt_archive_crc(self):
        compressed = self.engine.compress(b"Valid dataset to test CRC integrity check")
        corrupted = bytearray(compressed)
        # Flip a byte in the payload area
        corrupted[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            self.engine.decompress(bytes(corrupted))

if __name__ == "__main__":
    unittest.main()
