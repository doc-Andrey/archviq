import unittest

from profile_engine import compute_profile


class Engine43SmokeTest(unittest.TestCase):
    def test_profile_is_deterministic_and_bounded(self):
        a = compute_profile("Smoke", "1967-12-19")
        b = compute_profile("Smoke", "1967-12-19")
        self.assertEqual(a["scores"], b["scores"])
        self.assertEqual(a["x9"], b["x9"])
        self.assertEqual(a["central_conception"], "1967-03-28")
        self.assertEqual(set(a["scores"]), {
            "resource", "switching", "lock", "novelty", "control",
            "processing_cost", "maturation"
        })
        for value in a["scores"].values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
        for value in a["x9"].values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)


if __name__ == "__main__":
    unittest.main()
