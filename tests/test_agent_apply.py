import conftest_paths  # noqa: F401
import json, os, tempfile, unittest
import agentsetup as ag


class TestApply(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()

    def test_claude_creates_settings(self):
        r = ag.apply("claude-code", self.home, "http://127.0.0.1:8090", "", "big", "small")
        self.assertTrue(r["ok"])
        self.assertEqual(r["action"], "created")
        self.assertIsNone(r["backup"])
        data = json.load(open(r["path"], encoding="utf-8"))
        self.assertEqual(data["env"]["ANTHROPIC_MODEL"], "big")

    def test_json_merge_preserves_existing_and_backs_up(self):
        path = os.path.join(self.home, ".claude", "settings.json")
        os.makedirs(os.path.dirname(path))
        json.dump({"theme": "dark", "env": {"KEEP": "1"}}, open(path, "w"))
        r = ag.apply("claude-code", self.home, "http://127.0.0.1:8090", "", "big")
        self.assertEqual(r["action"], "merged")
        self.assertTrue(os.path.exists(r["backup"]))
        data = json.load(open(path, encoding="utf-8"))
        self.assertEqual(data["theme"], "dark")           # preserved
        self.assertEqual(data["env"]["KEEP"], "1")         # preserved
        self.assertEqual(data["env"]["ANTHROPIC_MODEL"], "big")  # added

    def test_pi_merge_preserves_other_providers(self):
        path = os.path.join(self.home, ".pi", "agent", "models.json")
        os.makedirs(os.path.dirname(path))
        json.dump({"providers": {"ollama": {"baseUrl": "x"}}}, open(path, "w"))
        ag.apply("pi", self.home, "http://127.0.0.1:8080/v1", "", "m")
        data = json.load(open(path, encoding="utf-8"))
        self.assertIn("ollama", data["providers"])
        self.assertEqual(data["providers"]["llamaforge"]["models"], [{"id": "m"}])

    def test_codex_appends_block_and_is_idempotent(self):
        r1 = ag.apply("codex", self.home, "http://127.0.0.1:8080/v1", "", "m")
        self.assertEqual(r1["action"], "created")
        text1 = open(r1["path"], encoding="utf-8").read()
        self.assertIn("[model_providers.llamaforge]", text1)
        r2 = ag.apply("codex", self.home, "http://127.0.0.1:8080/v1", "", "m")
        self.assertEqual(r2["action"], "present")           # already there, not duplicated
        text2 = open(r2["path"], encoding="utf-8").read()
        self.assertEqual(text1.count("[model_providers.llamaforge]"), 1)
        self.assertEqual(text2.count("[model_providers.llamaforge]"), 1)

    def test_codex_preserves_existing_top_level_model(self):
        path = os.path.join(self.home, ".codex", "config.toml")
        os.makedirs(os.path.dirname(path))
        open(path, "w").write('model = "existing"\n')
        ag.apply("codex", self.home, "http://127.0.0.1:8080/v1", "", "m")
        text = open(path, encoding="utf-8").read()
        self.assertIn('model = "existing"', text)           # untouched
        self.assertIn("[model_providers.llamaforge]", text)  # block appended
        # our model line is commented out so it doesn't override
        self.assertIn('# model = "m"', text)

    def test_unknown_agent_raises_no_write(self):
        with self.assertRaises(ValueError):
            ag.apply("nope", self.home, "http://x", "", "m")


if __name__ == "__main__":
    unittest.main()
