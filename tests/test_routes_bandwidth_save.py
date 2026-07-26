import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config


class TestBandwidthSave(unittest.TestCase):
    def setUp(self):
        self._cfg = config.CONFIG
        fd, self.tmp = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.tmp, "w", encoding="utf-8") as f:
            f.write("{}")
        config.CONFIG = self.tmp

    def tearDown(self):
        config.CONFIG = self._cfg
        try:
            os.remove(self.tmp)
        except OSError:
            pass

    def test_roundtrip(self):
        config.update({"vram_bandwidths": {"ram_bw": 80, "disk_bw": 12}})
        self.assertEqual(config.load()["vram_bandwidths"]["ram_bw"], 80)
        self.assertEqual(config.load()["vram_bandwidths"]["disk_bw"], 12)


if __name__ == "__main__":
    unittest.main()
