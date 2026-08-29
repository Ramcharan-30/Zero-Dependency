import unittest
from src.zcomp.profiler import profile_content
from src.zcomp.strategy import select_best_candidate, Profile
from src.zcomp.codecs import StoreCodec

class TestSelector(unittest.TestCase):
    def test_selector_picks_store_for_small_or_high_entropy_files(self):
        # Very small string where header overhead exceeds compressed payload gain
        data = b"hi"
        prof = profile_content(data)
        result = select_best_candidate("small.txt", data, prof, Profile.TXT)
        self.assertIsInstance(result.best_codec, StoreCodec)

    def test_selector_evaluates_candidates(self):
        # Repetitive text where compression should win over STORE
        data = b"ZeroShrink adaptive compression engine test string! " * 50
        prof = profile_content(data)
        result = select_best_candidate("test.txt", data, prof, Profile.TXT)
        self.assertGreater(len(result.evaluations), 1)
        self.assertLess(result.best_size, len(data))

if __name__ == "__main__":
    unittest.main()
