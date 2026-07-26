import conftest_paths  # noqa: F401
import unittest
from vramwise.physics import Model, Hardware, predict


# The measurement box the vramwise model is calibrated to: RTX 5080 16GB +
# 5060 Ti 16GB = 32GB VRAM, 31GB RAM, SN7100 ~5.7 GB/s NVMe. The effective
# vram_bw (500) is the dual-GPU sustained rate, NOT a single card's spec sheet.
# Ported verbatim from vramwise's own tests/test_anchors.py so this stays a true
# tripwire: if an upstream re-sync breaks calibration, these fail.
BOX = Hardware(name="measure-box", vram_gb=32, ram_gb=31, disk_bw=5.7,
               ram_bw=50.0, vram_bw=500.0)


def _within(pred, target, tol=0.20):
    return abs(pred - target) / target <= tol


class TestCalibrationAnchors(unittest.TestCase):
    """The two measured anchors vramwise reproduces. If a future upstream
    re-sync breaks these, the calibration changed and must be reviewed."""

    def test_glm52_streaming_anchor(self):
        # GLM-5.2 754B MoE, UD-IQ4_XS 3.88 bpw, ~3.4 GB active/token -> streamed 0.9 tok/s.
        glm = Model(name="GLM-5.2", total_params=754e9,
                    active_params=3.4e9 * 8 / 3.88, bpw=3.88, n_layers=92)
        p = predict(glm, BOX)
        self.assertEqual(p.regime, "streaming")
        self.assertTrue(_within(p.tok_s, 0.9),
                        f"GLM-5.2 predicted {p.tok_s:.2f} tok/s, measured 0.9")

    def test_air_resident_anchor(self):
        # GLM-4.5-Air 106B/12B active, UD-Q2_K_XL ~3.5 bpw ~47 GB, resident -> 19.5 tok/s.
        air = Model(name="GLM-4.5-Air", total_params=106e9, active_params=12e9,
                    bpw=3.5, n_layers=47)
        p = predict(air, BOX)
        self.assertIn(p.regime, ("hybrid", "gpu-resident"))
        self.assertTrue(_within(p.tok_s, 19.5),
                        f"GLM-Air predicted {p.tok_s:.2f} tok/s, measured 19.5")

    def test_regime_ordering_is_monotonic(self):
        # A model that fits fast memory must be predicted faster than one that streams.
        small = Model("small", 8e9, 8e9, bpw=4.8)
        huge = Model("huge", 700e9, 30e9, bpw=4.0)
        self.assertGreater(predict(small, BOX).tok_s, predict(huge, BOX).tok_s)


if __name__ == "__main__":
    unittest.main()
