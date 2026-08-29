import unittest
from pathlib import Path
from src.zcomp.archive import create_archive, extract_archive
from src.zcomp.errors import ArchiveValidationError

class TestCorruptionHandling(unittest.TestCase):
    def test_corrupted_payload_byte_rejection(self):
        data = b"Critical data stream that must not be corrupted!" * 20
        arc_bytes, selection, prof = create_archive(Path("critical.txt"), data)

        # Corrupt one payload byte near the end
        corrupted = bytearray(arc_bytes)
        corrupted[-5] ^= 0xFF
        corrupted_bytes = bytes(corrupted)

        with self.assertRaises(ArchiveValidationError) as ctx:
            extract_archive(corrupted_bytes)

        self.assertTrue(
            "CRC" in str(ctx.exception) or
            "SHA" in str(ctx.exception) or
            "failed" in str(ctx.exception) or
            "decompression" in str(ctx.exception).lower()
        )

    def test_truncated_archive_rejection(self):
        data = b"Sample payload" * 10
        arc_bytes, selection, prof = create_archive(Path("sample.txt"), data)

        truncated = arc_bytes[:15]
        with self.assertRaises(ArchiveValidationError):
            extract_archive(truncated)

    def test_invalid_magic_rejection(self):
        data = b"Sample payload"
        arc_bytes, selection, prof = create_archive(Path("sample.txt"), data)

        corrupted = b"BADM" + arc_bytes[4:]
        with self.assertRaises(ArchiveValidationError):
            extract_archive(corrupted)

if __name__ == "__main__":
    unittest.main()
