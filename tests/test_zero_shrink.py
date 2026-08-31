import unittest
from zero_shrink import ZeroShrinkEngine

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

if __name__ == "__main__":
    unittest.main()
