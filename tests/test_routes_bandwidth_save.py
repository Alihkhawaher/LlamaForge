import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config, routes


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

    def test_config_route_accepts_bandwidths(self):
        req = routes.Req(body={"vram_bandwidths": {"ram_bw": 80, "disk_bw": 12.5}})
        status, out = routes.post_config(req)
        self.assertEqual(status, 200)
        self.assertEqual(config.load()["vram_bandwidths"], {"ram_bw": 80.0, "disk_bw": 12.5})

    def test_config_route_empty_clears_overrides(self):
        config.update({"vram_bandwidths": {"ram_bw": 80}})
        routes.post_config(routes.Req(body={"vram_bandwidths": {}}))
        self.assertEqual(config.load()["vram_bandwidths"], {})

    def test_config_route_rejects_bad_bandwidth(self):
        with self.assertRaises(routes.ApiError):
            routes.post_config(routes.Req(body={"vram_bandwidths": {"ram_bw": -5}}))


if __name__ == "__main__":
    unittest.main()
