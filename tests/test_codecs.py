import unittest
from src.zcomp.codecs import (
    StoreCodec,
    HuffmanCodec,
    RleCodec,
    ZlibCodec,
    LzmaCodec,
    ZstdCodec,
    Bz2Codec
)

class TestCodecs(unittest.TestCase):
    def test_all_codecs_roundtrip(self):
        codecs = [
            StoreCodec(),
            HuffmanCodec(),
            RleCodec(),
            ZlibCodec(),
            LzmaCodec(),
            ZstdCodec(),
            Bz2Codec()
        ]

        test_payloads = [
            b"",
            b"A",
            b"Hello World!",
            b"The quick brown fox jumps over the lazy dog." * 10,
            b"A" * 500 + b"B" * 300,
            bytes(range(256))
        ]

        for codec in codecs:
            for data in test_payloads:
                meta, payload = codec.compress(data)
                restored = codec.decompress(meta, payload)
                self.assertEqual(
                    restored,
                    data,
                    f"Codec {codec.__class__.__name__} failed on data len {len(data)}"
                )

if __name__ == "__main__":
    unittest.main()
