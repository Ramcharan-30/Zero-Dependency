import unittest
from src.zcomp.profiler import (
    calculate_entropy,
    calculate_byte_diversity,
    calculate_printable_ratio,
    calculate_run_ratio,
    calculate_repetition_score,
    detect_signature,
    profile_content
)

class TestProfiler(unittest.TestCase):
    def test_entropy_zero(self):
        self.assertEqual(calculate_entropy(b"AAAAAAA"), 0.0)

    def test_entropy_high(self):
        # 256 distinct bytes in uniform sequence
        data = bytes(range(256))
        self.assertAlmostEqual(calculate_entropy(data), 8.0, places=2)

    def test_byte_diversity(self):
        self.assertEqual(calculate_byte_diversity(b"AAAA"), 1 / 256.0)
        data = bytes(range(256))
        self.assertEqual(calculate_byte_diversity(data), 1.0)

    def test_printable_ratio(self):
        self.assertEqual(calculate_printable_ratio(b"Hello World!\n"), 1.0)
        self.assertEqual(calculate_printable_ratio(bytes([0, 1, 2, 3])), 0.0)

    def test_run_ratio(self):
        self.assertGreater(calculate_run_ratio(b"AAAAAAAAAAAAAAAA"), 0.8)
        self.assertEqual(calculate_run_ratio(b"ABCDEFGH"), 0.0)

    def test_signature_detection(self):
        self.assertEqual(detect_signature(b"\x89PNG\r\n\x1a\nExtraData"), "PNG")
        self.assertEqual(detect_signature(b"%PDF-1.4 header"), "PDF")
        self.assertEqual(detect_signature(b"\xFF\xD8\xFFImage"), "JPEG")
        self.assertIsNone(detect_signature(b"Hello World"))

    def test_profile_content_classification(self):
        text_prof = profile_content(b"Hello World! This is standard ASCII text document content.")
        self.assertTrue(text_prof.is_text)

        rep_prof = profile_content(b"A" * 500)
        self.assertTrue(rep_prof.is_repetitive)

if __name__ == "__main__":
    unittest.main()
