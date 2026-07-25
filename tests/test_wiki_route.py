import conftest_paths  # noqa: F401
import os, tempfile, unittest
from unittest import mock
import config, wiki, routes


class TestWikiExportRoute(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._orig = config.CONFIG
        config.CONFIG = os.path.join(self.dir, "config.json")
        config.save({**config.load(), "wiki_dir": os.path.join(self.dir, "wiki")})

    def tearDown(self):
        config.CONFIG = self._orig

    def test_export_payload_builds_path_and_composes(self):
        wiki.write_doc("a", "alpha")
        wiki.save_profile("p", ["a"])
        home = self.dir
        with mock.patch.object(routes.os.path, "expanduser", return_value=home):
            out = routes._wiki_export({"agent": "claude-code", "profile": "p"})
        self.assertTrue(out["ok"])
        self.assertTrue(out["path"].endswith(os.path.join(".claude", "CLAUDE.md")))
        self.assertIn("alpha", open(out["path"], encoding="utf-8").read())

    def test_export_unknown_agent_without_path_errors(self):
        out = routes._wiki_export({"agent": "nope", "profile": ""})
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
