import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config


class TestDocsConfig(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._orig = config.CONFIG
        config.CONFIG = os.path.join(self.dir, "config.json")

    def tearDown(self):
        config.CONFIG = self._orig

    def test_default(self):
        self.assertEqual(config.load()["docs_dir"], "")

    def test_round_trip(self):
        config.save({**config.load(), "docs_dir": "/tmp/x"})
        self.assertEqual(config.load()["docs_dir"], "/tmp/x")


if __name__ == "__main__":
    unittest.main()
