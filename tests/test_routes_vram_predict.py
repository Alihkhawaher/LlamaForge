import conftest_paths  # noqa: F401
import unittest
import routes, vram_predict, hub


class TestVramPredictRoute(unittest.TestCase):
    def setUp(self):
        self._pred = vram_predict.predict_remote
        self._files = hub.files
        vram_predict.predict_remote = lambda **kw: {
            "regime": "streaming", "tok_s": 0.9, "confidence": "high", "note": "streams"}
        hub.files = lambda repo, vram: {"files": [], "mmproj": []}

    def tearDown(self):
        vram_predict.predict_remote = self._pred
        hub.files = self._files

    def test_predict_route(self):
        req = routes.Req(body={"repo": "acme/big", "quant": "iq4_xs"})
        status, payload = routes.post_vram_predict(req)
        self.assertEqual(status, 200)
        self.assertEqual(payload["regime"], "streaming")

    def test_registered(self):
        self.assertIn("/api/vram/predict", routes.POST_ROUTES)

    def test_size_fallback_picks_matching_gguf(self):
        # When config.json lacks geometry, the panel falls back to the file size.
        # The file whose name matches the requested quant is chosen (else the largest).
        captured = {}
        hub.files = lambda repo, vram: {"files": [
            {"path": "M-Q4_K_M.gguf", "size": 5_000_000_000},
            {"path": "M-Q8_0.gguf", "size": 9_000_000_000}], "mmproj": []}

        def cap(**kw):
            captured.update(kw)
            return {"regime": "hybrid", "tok_s": 10.0, "confidence": "low", "note": "x"}
        vram_predict.predict_remote = cap

        routes.post_vram_predict(routes.Req(body={"repo": "acme/m", "quant": "q8_0"}))
        self.assertEqual(captured["size_bytes"], 9_000_000_000)
        self.assertEqual(captured["gguf_file"], "M-Q8_0.gguf")

    def test_no_files_leaves_size_none(self):
        captured = {}

        def cap(**kw):
            captured.update(kw)
            return {"regime": "streaming", "tok_s": 0.9, "confidence": "high", "note": "x"}
        vram_predict.predict_remote = cap
        routes.post_vram_predict(routes.Req(body={"repo": "acme/m", "quant": "q4_k_m"}))
        self.assertIsNone(captured["size_bytes"])


if __name__ == "__main__":
    unittest.main()
