import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config


class TestAnthropicConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._orig = config.CONFIG
        config.CONFIG = os.path.join(self.dir, "config.json")

    def tearDown(self):
        config.CONFIG = self._orig

    def test_defaults_present(self):
        c = config.load()
        self.assertEqual(c["anthropic_default_model"], "")
        self.assertIs(c["anthropic_shim_enabled"], True)


if __name__ == "__main__":
    unittest.main()
