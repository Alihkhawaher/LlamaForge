# tests/test_anthropic_stream_route.py
import conftest_paths  # noqa: F401
import unittest
import routes


class TestStreamWriter(unittest.TestCase):
    def test_writes_translated_events(self):
        chunks = []

        def write(b):
            chunks.append(b)

        lines = [
            b'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            b"data: [DONE]",
        ]
        routes._write_anthropic_stream(write, "m", 200, lines)
        blob = b"".join(chunks).decode()
        self.assertIn("event: message_start", blob)
        self.assertIn("event: content_block_delta", blob)
        self.assertIn("event: message_stop", blob)

    def test_upstream_error_before_stream_emits_error_event(self):
        chunks = []
        # status >= 400 means resp is an error dict, not a line iterator
        routes._write_anthropic_stream(lambda b: chunks.append(b), "m", 500,
                                       {"error": "boom"})
        blob = b"".join(chunks).decode()
        self.assertIn("event: error", blob)
        self.assertIn("boom", blob)


if __name__ == "__main__":
    unittest.main()
