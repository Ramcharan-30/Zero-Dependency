import unittest
from src.zcomp.transforms.rle import RleTransform
from src.zcomp.codecs.rle import RleCodec

class TestRLE(unittest.TestCase):
    def test_rle_transform_roundtrip(self):
        transform = RleTransform()
        samples = [
            b"",
            b"A",
            b"AA",
            b"AAAAAA",
            b"AAAAAAAAAAAAAAAABBBBBBBCCCCDDDD",
            b"ABCDEFGH12345678",
            bytes(range(256))
        ]
        for data in samples:
            meta, transformed = transform.transform(data)
            restored = transform.inverse(meta, transformed)
            self.assertEqual(restored, data, f"Failed RLE transform roundtrip for {data[:20]}")

    def test_rle_codec_roundtrip(self):
        codec = RleCodec()
        samples = [
            b"",
            b"X",
            b"XXXXYYYYZZZZ",
            b"Hello World"
        ]
        for data in samples:
            meta, payload = codec.compress(data)
            restored = codec.decompress(meta, payload)
            self.assertEqual(restored, data, f"Failed RleCodec roundtrip for {data}")

if __name__ == "__main__":
    unittest.main()
