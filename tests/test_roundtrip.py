import unittest
from pathlib import Path
from src.zcomp.archive import create_archive, extract_archive

class TestEndToEndRoundtrip(unittest.TestCase):
    def test_text_file_roundtrip(self):
        data = b"ZeroShrink adaptive compression roundtrip text content.\n" * 50
        arc_bytes, selection, prof = create_archive(Path("doc.txt"), data)
        name, restored, header, v_result = extract_archive(arc_bytes)
        self.assertEqual(name, "doc.txt")
        self.assertEqual(restored, data)
        self.assertTrue(v_result.is_valid)

    def test_binary_file_roundtrip(self):
        data = bytes(i % 256 for i in range(5000))
        arc_bytes, selection, prof = create_archive(Path("data.bin"), data)
        name, restored, header, v_result = extract_archive(arc_bytes)
        self.assertEqual(name, "data.bin")
        self.assertEqual(restored, data)
        self.assertTrue(v_result.is_valid)

    def test_repetitive_file_roundtrip(self):
        data = b"RLE_TRANSFORM_TEST_" * 200
        arc_bytes, selection, prof = create_archive(Path("rep.dat"), data)
        name, restored, header, v_result = extract_archive(arc_bytes)
        self.assertEqual(restored, data)
        self.assertTrue(v_result.is_valid)

if __name__ == "__main__":
    unittest.main()
