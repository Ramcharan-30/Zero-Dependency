import unittest
from src.zcomp.transforms.shuffle import Shuffle32Transform, Shuffle64Transform

class TestShuffleTransform(unittest.TestCase):
    def test_shuffle32_roundtrip(self):
        shuf32 = Shuffle32Transform()
        samples = [
            b"",
            b"1234",
            b"12345678",
            b"123456789",  # With remainder byte
            bytes(range(100))
        ]
        for data in samples:
            meta, transformed = shuf32.transform(data)
            restored = shuf32.inverse(meta, transformed)
            self.assertEqual(restored, data)

    def test_shuffle64_roundtrip(self):
        shuf64 = Shuffle64Transform()
        samples = [
            b"",
            b"12345678",
            b"1234567887654321",
            bytes(range(200))
        ]
        for data in samples:
            meta, transformed = shuf64.transform(data)
            restored = shuf64.inverse(meta, transformed)
            self.assertEqual(restored, data)

if __name__ == "__main__":
    unittest.main()
