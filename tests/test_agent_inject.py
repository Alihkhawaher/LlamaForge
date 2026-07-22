import conftest_paths  # noqa: F401
import unittest
import agentsetup as ag


class TestAgentInject(unittest.TestCase):
    def test_codex_inject_uses_given_endpoint(self):
        # caller passes the panel proxy endpoint when inject is on
        r = ag.generate("codex", "http://127.0.0.1:8090/v1", "", "m", inject=True)
        self.assertIn('base_url = "http://127.0.0.1:8090/v1"', r["content"])

    def test_inject_flag_optional_default_false(self):
        r = ag.generate("codex", "http://127.0.0.1:8080/v1", "", "m")
        self.assertIn('base_url = "http://127.0.0.1:8080/v1"', r["content"])


if __name__ == "__main__":
    unittest.main()
