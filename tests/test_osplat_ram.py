import conftest_paths  # noqa: F401
import unittest
import osplat


class TestTotalRam(unittest.TestCase):
    def test_returns_positive_or_zero(self):
        n = osplat.total_ram_bytes()
        self.assertIsInstance(n, int)
        self.assertGreaterEqual(n, 0)

    def test_parse_meminfo(self):
        text = "MemTotal:       32791234 kB\nMemFree: 100 kB\n"
        self.assertEqual(osplat.parse_meminfo(text), 32791234 * 1024)

    def test_parse_meminfo_missing(self):
        self.assertEqual(osplat.parse_meminfo("nope\n"), 0)


if __name__ == "__main__":
    unittest.main()
