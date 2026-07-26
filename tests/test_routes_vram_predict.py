import conftest_paths  # noqa: F401
import unittest
import routes, vram_predict


class TestVramPredictRoute(unittest.TestCase):
    def setUp(self):
        self._pred = vram_predict.predict_remote
        vram_predict.predict_remote = lambda **kw: {
            "regime": "streaming", "tok_s": 0.9, "confidence": "high", "note": "streams"}

    def tearDown(self):
        vram_predict.predict_remote = self._pred

    def test_predict_route(self):
        req = routes.Req(body={"repo": "acme/big", "quant": "iq4_xs"})
        status, payload = routes.post_vram_predict(req)
        self.assertEqual(status, 200)
        self.assertEqual(payload["regime"], "streaming")

    def test_registered(self):
        self.assertIn("/api/vram/predict", routes.POST_ROUTES)


if __name__ == "__main__":
    unittest.main()
