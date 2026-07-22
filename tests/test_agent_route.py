# tests/test_agent_route.py
import conftest_paths  # noqa: F401
import os, tempfile, unittest
from unittest import mock
import server


CFG = {"router_host": "127.0.0.1", "router_api_key": "", "router_port": 8080,
       "panel_port": 8090}


class TestAgentEndpoint(unittest.TestCase):
    def test_claude_uses_panel_port(self):
        with mock.patch.object(server, "cfg", return_value=CFG):
            self.assertEqual(server._agent_endpoint("claude-code"), "http://127.0.0.1:8090")

    def test_codex_uses_router_v1(self):
        with mock.patch.object(server, "cfg", return_value=CFG):
            self.assertEqual(server._agent_endpoint("codex"), "http://127.0.0.1:8080/v1")

    def test_lan_uses_lan_ip(self):
        lan = {**CFG, "router_host": "0.0.0.0"}
        with mock.patch.object(server, "cfg", return_value=lan), \
             mock.patch.object(server.router_ctl, "lan_ip", return_value="192.168.1.5"):
            self.assertEqual(server._agent_endpoint("pi"), "http://192.168.1.5:8080/v1")


if __name__ == "__main__":
    unittest.main()
