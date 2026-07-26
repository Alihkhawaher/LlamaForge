import conftest_paths  # noqa: F401
import unittest
import vram_predict as vp
from vramwise import constants as C


class TestBuildHardware(unittest.TestCase):
    def test_preset_bandwidth_from_gpu_name(self):
        self.assertEqual(vp._preset_vram_bw("NVIDIA GeForce RTX 4090"), 1008)
        self.assertEqual(vp._preset_vram_bw("NVIDIA GeForce RTX 5080"), 960)

    def test_unknown_gpu_falls_back_to_default(self):
        self.assertEqual(vp._preset_vram_bw("Some Weird Card"), C.DEFAULT_VRAM_BW)

    def test_overrides_win(self):
        cfg = {"vram_bandwidths": {"ram_bw": 80, "disk_bw": 12}}
        hw = vp.build_hardware(cfg=cfg, gpus=[{"name": "RTX 4090", "vram_mib": 24576}],
                               ram_gb=64.0)
        self.assertEqual(hw.ram_bw, 80)
        self.assertEqual(hw.disk_bw, 12)
        self.assertEqual(hw.vram_bw, 1008)
        self.assertAlmostEqual(hw.vram_gb, 24.0, delta=0.1)
        self.assertEqual(hw.ram_gb, 64.0)


if __name__ == "__main__":
    unittest.main()
