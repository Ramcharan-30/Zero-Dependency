import unittest
from src.zcomp.archive import (
    MAGIC,
    VERSION,
    serialize_archive,
    deserialize_archive
)

class TestArchiveFormat(unittest.TestCase):
    def test_serialize_and_deserialize_headers(self):
        filename = "test_document.txt"
        orig_data = b"Sample text content for serialization test."
        payload = b"compressed_payload_bytes"
        meta = b"transform_meta"

        arc_bytes = serialize_archive(
            filename=filename,
            original_data=orig_data,
            profile_id=1,
            transform_id=0,
            codec_id=5,
            codec_level=0,
            transform_meta=meta,
            payload=payload
        )

        header, read_payload = deserialize_archive(arc_bytes)
        self.assertEqual(header.magic, MAGIC)
        self.assertIn(header.version, (2, 3))
        self.assertEqual(header.filename, filename)
        self.assertEqual(header.orig_size, len(orig_data))
        self.assertEqual(read_payload, payload)

if __name__ == "__main__":
    unittest.main()
