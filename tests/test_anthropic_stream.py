import conftest_paths  # noqa: F401
import json, unittest
import anthropic_shim as sh


def parse(events):
    """[(event_name, data_dict), ...] from the shim's SSE byte output."""
    out = []
    for raw in events:
        s = raw.decode()
        name = s.split("\n", 1)[0].split("event: ", 1)[1]
        data = json.loads(s.split("data: ", 1)[1].strip())
        out.append((name, data))
    return out


def oai(obj):
    return "data: " + json.dumps(obj)


class TestStream(unittest.TestCase):
    def test_text_stream_sequence(self):
        lines = [
            oai({"choices": [{"delta": {"content": "Hel"}, "finish_reason": None}]}),
            oai({"choices": [{"delta": {"content": "lo"}, "finish_reason": None}]}),
            oai({"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"completion_tokens": 2}}),
            "data: [DONE]",
        ]
        ev = parse(sh.stream_anthropic_events(lines, "m"))
        names = [n for n, _ in ev]
        self.assertEqual(names, ["message_start", "content_block_start",
            "content_block_delta", "content_block_delta", "content_block_stop",
            "message_delta", "message_stop"])
        self.assertEqual(ev[2][1]["delta"], {"type": "text_delta", "text": "Hel"})
        self.assertEqual(ev[5][1]["delta"]["stop_reason"], "end_turn")
        self.assertEqual(ev[5][1]["usage"]["output_tokens"], 2)

    def test_tool_call_stream(self):
        lines = [
            oai({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "id": "t1", "function": {"name": "f", "arguments": ""}}]}}]}),
            oai({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": '{"x":'}}]}}]}),
            oai({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": "1}"}}]}}]}),
            oai({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}),
            "data: [DONE]",
        ]
        ev = parse(sh.stream_anthropic_events(lines, "m"))
        names = [n for n, _ in ev]
        self.assertEqual(names, ["message_start", "content_block_start",
            "content_block_delta", "content_block_delta", "content_block_stop",
            "message_delta", "message_stop"])
        self.assertEqual(ev[1][1]["content_block"], {"type": "tool_use", "id": "t1", "name": "f", "input": {}})
        self.assertEqual(ev[2][1]["delta"], {"type": "input_json_delta", "partial_json": '{"x":'})
        self.assertEqual(ev[3][1]["delta"], {"type": "input_json_delta", "partial_json": "1}"})
        self.assertEqual(ev[5][1]["delta"]["stop_reason"], "tool_use")

    def test_text_then_tool_closes_text_block(self):
        lines = [
            oai({"choices": [{"delta": {"content": "hi"}}]}),
            oai({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "id": "t1", "function": {"name": "f", "arguments": "{}"}}]}}]}),
            oai({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}),
            "data: [DONE]",
        ]
        ev = parse(sh.stream_anthropic_events(lines, "m"))
        names = [n for n, _ in ev]
        # text block opens+delta+stop, then tool block opens+delta+stop
        self.assertEqual(names, ["message_start",
            "content_block_start", "content_block_delta", "content_block_stop",
            "content_block_start", "content_block_delta", "content_block_stop",
            "message_delta", "message_stop"])
        self.assertEqual(ev[1][1]["content_block"]["type"], "text")
        self.assertEqual(ev[1][1]["index"], 0)
        self.assertEqual(ev[4][1]["content_block"]["type"], "tool_use")
        self.assertEqual(ev[4][1]["index"], 1)

    def test_empty_stream_still_valid(self):
        ev = parse(sh.stream_anthropic_events(["data: [DONE]"], "m"))
        self.assertEqual([n for n, _ in ev], ["message_start", "message_delta", "message_stop"])


if __name__ == "__main__":
    unittest.main()
