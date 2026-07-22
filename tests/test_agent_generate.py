import conftest_paths  # noqa: F401
import json, unittest
import agentsetup as ag


class TestGenerate(unittest.TestCase):
    def test_claude_code_settings(self):
        r = ag.generate("claude-code", "http://127.0.0.1:8090", "", "big", "small")
        self.assertEqual(r["format"], "json")
        self.assertEqual(r["target_path"], "~/.claude/settings.json")
        env = json.loads(r["content"])["env"]
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8090")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "llamaforge")  # placeholder when no key
        self.assertEqual(env["ANTHROPIC_MODEL"], "big")
        self.assertEqual(env["ANTHROPIC_SMALL_FAST_MODEL"], "small")

    def test_claude_code_uses_key_when_set(self):
        r = ag.generate("claude-code", "http://127.0.0.1:8090", "secret", "big")
        env = json.loads(r["content"])["env"]
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "secret")
        # small defaults to main model when omitted
        self.assertEqual(env["ANTHROPIC_SMALL_FAST_MODEL"], "big")

    def test_codex_toml(self):
        r = ag.generate("codex", "http://127.0.0.1:8080/v1", "", "m")
        self.assertEqual(r["format"], "toml")
        self.assertEqual(r["target_path"], "~/.codex/config.toml")
        self.assertIn("[model_providers.llamaforge]", r["content"])
        self.assertIn('base_url = "http://127.0.0.1:8080/v1"', r["content"])
        self.assertIn('wire_api = "chat"', r["content"])
        self.assertIn('model = "m"', r["content"])
        self.assertIn('model_provider = "llamaforge"', r["content"])
        self.assertNotIn("env_key", r["content"])  # no key -> no env_key

    def test_codex_env_key_when_set(self):
        r = ag.generate("codex", "http://127.0.0.1:8080/v1", "secret", "m")
        self.assertIn('env_key = "LLAMAFORGE_API_KEY"', r["content"])

    def test_pi_models_json(self):
        r = ag.generate("pi", "http://127.0.0.1:8080/v1", "", "m")
        self.assertEqual(r["format"], "json")
        self.assertEqual(r["target_path"], "~/.pi/agent/models.json")
        prov = json.loads(r["content"])["providers"]["llamaforge"]
        self.assertEqual(prov["baseUrl"], "http://127.0.0.1:8080/v1")
        self.assertEqual(prov["api"], "openai-completions")
        self.assertEqual(prov["models"], [{"id": "m"}])

    def test_unknown_agent_raises(self):
        with self.assertRaises(ValueError):
            ag.generate("nope", "http://x", "", "m")


if __name__ == "__main__":
    unittest.main()
