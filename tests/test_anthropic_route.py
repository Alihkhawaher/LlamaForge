import conftest_paths  # noqa: F401
import unittest
from unittest import mock
import server


class TestAnthropicRoute(unittest.TestCase):
    def test_nonstream_happy_path(self):
        oai_resp = {"id": "c1", "choices": [{"message": {"content": "hi"},
                    "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 1}}
        with mock.patch.object(server, "model_state",
                               return_value={"models": [{"id": "local-m"}]}), \
             mock.patch.object(server, "cfg", return_value={"router_host": "127.0.0.1",
                               "router_api_key": "", "anthropic_default_model": "",
                               "anthropic_shim_enabled": True, "router_port": 8080}), \
             mock.patch.object(server, "_router_openai", return_value=(200, oai_resp)) as ro:
            status, body = server._anthropic_messages(
                {"model": "local-m", "max_tokens": 10,
                 "messages": [{"role": "user", "content": "hi"}]}, {})
        self.assertEqual(status, 200)
        self.assertEqual(body["type"], "message")
        self.assertEqual(body["content"], [{"type": "text", "text": "hi"}])
        # forwarded model preserved
        self.assertEqual(ro.call_args[0][0]["model"], "local-m")

    def test_unknown_model_falls_back_to_default(self):
        oai_resp = {"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}]}
        with mock.patch.object(server, "model_state",
                               return_value={"models": [{"id": "local-m"}]}), \
             mock.patch.object(server, "cfg", return_value={"router_host": "127.0.0.1",
                               "router_api_key": "", "anthropic_default_model": "local-m",
                               "anthropic_shim_enabled": True, "router_port": 8080}), \
             mock.patch.object(server, "_router_openai", return_value=(200, oai_resp)) as ro:
            status, body = server._anthropic_messages(
                {"model": "claude-3-5-sonnet", "max_tokens": 10,
                 "messages": [{"role": "user", "content": "hi"}]}, {})
        self.assertEqual(status, 200)
        self.assertEqual(ro.call_args[0][0]["model"], "local-m")  # fell back

    def test_router_error_becomes_anthropic_error(self):
        with mock.patch.object(server, "model_state",
                               return_value={"models": [{"id": "local-m"}]}), \
             mock.patch.object(server, "cfg", return_value={"router_host": "127.0.0.1",
                               "router_api_key": "", "anthropic_default_model": "",
                               "anthropic_shim_enabled": True, "router_port": 8080}), \
             mock.patch.object(server, "_router_openai", return_value=(500, {"error": "boom"})):
            status, body = server._anthropic_messages(
                {"model": "local-m", "max_tokens": 10,
                 "messages": [{"role": "user", "content": "hi"}]}, {})
        self.assertEqual(status, 500)
        self.assertEqual(body["type"], "error")
        self.assertEqual(body["error"]["type"], "api_error")

    def test_lan_key_mismatch_401(self):
        with mock.patch.object(server, "cfg", return_value={"router_host": "0.0.0.0",
                               "router_api_key": "secret", "anthropic_default_model": "",
                               "anthropic_shim_enabled": True, "router_port": 8080}):
            self.assertFalse(server._shim_auth_ok({"x-api-key": "wrong"}))
            self.assertTrue(server._shim_auth_ok({"x-api-key": "secret"}))

    def test_localhost_auth_open(self):
        with mock.patch.object(server, "cfg", return_value={"router_host": "127.0.0.1",
                               "router_api_key": "secret", "router_port": 8080}):
            self.assertTrue(server._shim_auth_ok({}))


if __name__ == "__main__":
    unittest.main()
