import conftest_paths  # noqa: F401
import unittest
import hardware, osplat


class TestDetectRamGb(unittest.TestCase):
    def test_converts_bytes_to_gb(self):
        orig = osplat.total_ram_bytes
        osplat.total_ram_bytes = lambda: 32 * 1000 * 1000 * 1000
        try:
            self.assertAlmostEqual(hardware.detect_ram_gb(), 32.0, delta=0.1)
        finally:
            osplat.total_ram_bytes = orig

    def test_zero_when_unknown(self):
        orig = osplat.total_ram_bytes
        osplat.total_ram_bytes = lambda: 0
        try:
            self.assertEqual(hardware.detect_ram_gb(), 0.0)
        finally:
            osplat.total_ram_bytes = orig


if __name__ == "__main__":
    unittest.main()
