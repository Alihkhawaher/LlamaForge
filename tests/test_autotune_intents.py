import conftest_paths  # noqa: F401
import unittest
import autotune

MIB = 1024 * 1024


def gpu(vram_mib, cc="8.6"):
    return {"vram_mib": vram_mib, "compute_cap": cc}


def hw1():
    return {"gpus": [gpu(24000)], "cpu": {"threads": 24, "cores": 12}}


META = {"block_count": 32, "context_length": 128000}
SIZE = 5 * 1024 * MIB


class TestIntents(unittest.TestCase):
    def test_context_uses_quantized_kv_and_large_ctx(self):
        r = autotune.recommend(META, hw1(), "context", size_bytes=SIZE)
        self.assertEqual(r["knobs"]["cache-type-k"], "q8_0")
        self.assertEqual(r["knobs"]["cache-type-v"], "q8_0")
        self.assertEqual(r["knobs"]["ctx-size"], "128000")

    def test_speed_uses_f16_kv_and_batch(self):
        r = autotune.recommend(META, hw1(), "speed", size_bytes=SIZE)
        self.assertEqual(r["knobs"]["cache-type-k"], "f16")
        self.assertEqual(r["knobs"]["batch-size"], "2048")
        self.assertEqual(r["knobs"]["ubatch-size"], "512")
        self.assertEqual(r["knobs"]["ctx-size"], "16384")

    def test_coding_sets_deterministic_sampling(self):
        r = autotune.recommend(META, hw1(), "coding", size_bytes=SIZE)
        self.assertEqual(r["knobs"]["temp"], "0.2")
        self.assertEqual(r["knobs"]["top-p"], "0.9")

    def test_balanced_adds_no_extra_knobs(self):
        r = autotune.recommend(META, hw1(), "balanced", size_bytes=SIZE)
        self.assertNotIn("cache-type-k", r["knobs"])
        self.assertNotIn("temp", r["knobs"])

    def test_multi_gpu_sets_tensor_split(self):
        hw = {"gpus": [gpu(24000), gpu(8000)], "cpu": {"threads": 24}}
        r = autotune.recommend(META, hw, "balanced", size_bytes=SIZE)
        self.assertEqual(r["knobs"]["tensor-split"], "24,8")


if __name__ == "__main__":
    unittest.main()
