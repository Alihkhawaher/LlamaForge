# tests/test_wiki_inject.py
import conftest_paths  # noqa: F401
import unittest
import server


class TestInject(unittest.TestCase):
    def test_openai_inject_prepends_system(self):
        body = {"model": "m", "messages": [{"role": "user", "content": "hi"}]}
        out = server._inject_openai_system(body, "CONTEXT")
        self.assertEqual(out["messages"][0], {"role": "system", "content": "CONTEXT"})
        self.assertEqual(out["messages"][1], {"role": "user", "content": "hi"})

    def test_openai_inject_merges_existing_system(self):
        body = {"messages": [{"role": "system", "content": "orig"},
                             {"role": "user", "content": "hi"}]}
        out = server._inject_openai_system(body, "CTX")
        self.assertEqual(out["messages"][0]["content"], "CTX\n\norig")
        self.assertEqual(len(out["messages"]), 2)

    def test_openai_inject_empty_composed_is_noop(self):
        body = {"messages": [{"role": "user", "content": "hi"}]}
        self.assertEqual(server._inject_openai_system(body, ""), body)

    def test_anthropic_inject_string_system(self):
        out = server._inject_anthropic_system({"system": "orig"}, "CTX")
        self.assertEqual(out["system"], "CTX\n\norig")

    def test_anthropic_inject_no_system(self):
        out = server._inject_anthropic_system({}, "CTX")
        self.assertEqual(out["system"], "CTX")

    def test_anthropic_inject_empty_noop(self):
        self.assertEqual(server._inject_anthropic_system({"system": "x"}, ""), {"system": "x"})


if __name__ == "__main__":
    unittest.main()
