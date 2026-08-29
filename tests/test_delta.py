import unittest
from src.zcomp.transforms.delta import Delta8Transform

class TestDelta8Transform(unittest.TestCase):
    def setUp(self):
        self.transform = Delta8Transform()

    def test_empty(self):
        meta, transformed = self.transform.transform(b"")
        restored = self.transform.inverse(meta, transformed)
        self.assertEqual(restored, b"")

    def test_single_byte(self):
        data = b"\x42"
        meta, transformed = self.transform.transform(data)
        restored = self.transform.inverse(meta, transformed)
        self.assertEqual(restored, data)

    def test_increasing_sequence(self):
        data = bytes([100, 101, 102, 103, 104, 105])
        meta, transformed = self.transform.transform(data)
        self.assertEqual(transformed, bytes([100, 1, 1, 1, 1, 1]))
        restored = self.transform.inverse(meta, transformed)
        self.assertEqual(restored, data)

    def test_all_256_bytes(self):
        data = bytes(range(256))
        meta, transformed = self.transform.transform(data)
        restored = self.transform.inverse(meta, transformed)
        self.assertEqual(restored, data)

    def test_constant_data(self):
        data = b"A" * 100
        meta, transformed = self.transform.transform(data)
        self.assertEqual(transformed[0], ord('A'))
        self.assertTrue(all(b == 0 for b in transformed[1:]))
        restored = self.transform.inverse(meta, transformed)
        self.assertEqual(restored, data)

if __name__ == "__main__":
    unittest.main()
