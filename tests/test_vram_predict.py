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


class TestPredictLocal(unittest.TestCase):
    def _hw(self):
        return vp.build_hardware(cfg={}, gpus=[{"name": "RTX 5090", "vram_mib": 32768}],
                                 ram_gb=64.0)

    def test_dense_model_from_meta(self):
        meta = {"name": "llama-8b", "quantization": "Q4_K_M", "block_count": 32}
        size = int(8e9 * 4.9 / 8)
        out = vp.predict_local("x.gguf", size_bytes=size, cfg={}, hw=self._hw(), meta=meta)
        self.assertEqual(out["regime"], "gpu-resident")
        self.assertEqual(out["confidence"], "high")
        self.assertGreater(out["tok_s"], 0)

    def test_moe_active_less_than_total(self):
        meta = {"name": "moe", "quantization": "Q4_K_M", "block_count": 48,
                "expert_count": 128, "expert_used_count": 8}
        m, conf = vp._model_from_gguf(meta, int(100e9 * 4.9 / 8))
        self.assertTrue(m.is_moe)
        self.assertLess(m.active_params, m.total_params)
        self.assertEqual(conf, "high")

    def test_missing_size_is_unknown(self):
        out = vp.predict_local("x.gguf", size_bytes=0, cfg={}, hw=self._hw(), meta={})
        self.assertEqual(out["confidence"], "unknown")
        self.assertIsNone(out["tok_s"])

    def test_unknown_quant_degrades_to_estimate(self):
        meta = {"name": "m", "quantization": "ZZ_WEIRD", "block_count": 32}
        m, conf = vp._model_from_gguf(meta, int(7e9 * 4.8 / 8))
        self.assertEqual(conf, "estimate")
        self.assertIsNotNone(m)


if __name__ == "__main__":
    unittest.main()
