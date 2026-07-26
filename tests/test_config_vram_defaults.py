import conftest_paths  # noqa: F401
import unittest
import config


class TestVramDefaults(unittest.TestCase):
    def test_defaults_present(self):
        c = config.load()
        self.assertIn("vram_bandwidths", c)
        self.assertIsInstance(c["vram_bandwidths"], dict)
        self.assertIn("vram_predict_enabled", c)
        self.assertTrue(c["vram_predict_enabled"])

    def test_bandwidths_default_isolated(self):
        a = config.load()
        a["vram_bandwidths"]["ram_bw"] = 999
        b = config.load()
        self.assertNotIn("ram_bw", b["vram_bandwidths"])


if __name__ == "__main__":
    unittest.main()
