import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config


class TestWikiConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._orig = config.CONFIG
        config.CONFIG = os.path.join(self.dir, "config.json")

    def tearDown(self):
        config.CONFIG = self._orig

    def test_defaults(self):
        c = config.load()
        self.assertEqual(c["wiki_dir"], "")
        self.assertEqual(c["wiki_profiles"], {})
        self.assertEqual(c["wiki_active"], {})


if __name__ == "__main__":
    unittest.main()
