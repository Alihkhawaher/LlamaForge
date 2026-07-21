import conftest_paths  # noqa: F401
import unittest
import anthropic_shim as sh


class TestResponseTranslation(unittest.TestCase):
    def test_text_response(self):
        o = {"id": "cmpl-1", "choices": [{"message": {"content": "hello"},
             "finish_reason": "stop"}], "usage": {"prompt_tokens": 5, "completion_tokens": 2}}
        a = sh.to_anthropic_response(o, "m")
        self.assertEqual(a["type"], "message")
        self.assertEqual(a["role"], "assistant")
        self.assertEqual(a["model"], "m")
        self.assertEqual(a["content"], [{"type": "text", "text": "hello"}])
        self.assertEqual(a["stop_reason"], "end_turn")
        self.assertEqual(a["usage"], {"input_tokens": 5, "output_tokens": 2})

    def test_tool_use_response(self):
        o = {"choices": [{"message": {"content": None, "tool_calls": [
            {"id": "t1", "function": {"name": "f", "arguments": '{"x":1}'}}]},
            "finish_reason": "tool_calls"}]}
        a = sh.to_anthropic_response(o, "m")
        self.assertEqual(a["stop_reason"], "tool_use")
        self.assertEqual(a["content"][0], {"type": "tool_use", "id": "t1", "name": "f", "input": {"x": 1}})

    def test_stop_reason_mapping(self):
        self.assertEqual(sh.map_stop_reason("stop"), "end_turn")
        self.assertEqual(sh.map_stop_reason("length"), "max_tokens")
        self.assertEqual(sh.map_stop_reason("tool_calls"), "tool_use")
        self.assertEqual(sh.map_stop_reason("weird"), "end_turn")

    def test_count_tokens_positive(self):
        n = sh.count_tokens_estimate({"model": "m",
            "messages": [{"role": "user", "content": "hello world this is a longer prompt"}]})
        self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
