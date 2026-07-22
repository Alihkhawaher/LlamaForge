import conftest_paths  # noqa: F401
import os, tempfile, unittest
import config, wiki


class TestWikiCore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._orig = config.CONFIG
        config.CONFIG = os.path.join(self.dir, "config.json")
        self.wdir = os.path.join(self.dir, "wiki")
        config.save({**config.load(), "wiki_dir": self.wdir})

    def tearDown(self):
        config.CONFIG = self._orig

    def test_doc_write_list_read_delete(self):
        wiki.write_doc("style", "be terse")
        self.assertEqual(wiki.list_docs(), ["style.md"])
        self.assertEqual(wiki.read_doc("style"), "be terse")
        self.assertTrue(wiki.delete_doc("style"))
        self.assertEqual(wiki.list_docs(), [])

    def test_safe_name_rejects_traversal(self):
        for bad in ["../evil", "a/b", "..", "", "  "]:
            with self.assertRaises(ValueError):
                wiki.write_doc(bad, "x")

    def test_safe_name_appends_md(self):
        wiki.write_doc("notes", "hi")
        self.assertTrue(os.path.exists(os.path.join(self.wdir, "notes.md")))

    def test_profiles_save_get_delete(self):
        wiki.save_profile("coding", ["style"], "coding rules")
        self.assertEqual(wiki.get_profiles()["coding"]["docs"], ["style.md"])
        self.assertEqual(wiki.get_profiles()["coding"]["description"], "coding rules")
        self.assertTrue(wiki.delete_profile("coding"))
        self.assertNotIn("coding", wiki.get_profiles())

    def test_compose_orders_and_headers(self):
        wiki.write_doc("a", "alpha")
        wiki.write_doc("b", "beta")
        wiki.save_profile("p", ["b", "a"])   # explicit order b then a
        out = wiki.compose("p")
        self.assertEqual(out, "## b\n\nbeta\n\n## a\n\nalpha")

    def test_compose_skips_missing_and_empty(self):
        wiki.write_doc("a", "alpha")
        wiki.write_doc("blank", "   ")
        wiki.save_profile("p", ["a", "blank", "gone"])
        self.assertEqual(wiki.compose("p"), "## a\n\nalpha")

    def test_compose_unknown_profile_empty(self):
        self.assertEqual(wiki.compose(""), "")
        self.assertEqual(wiki.compose("nope"), "")

    def test_active_round_trip(self):
        wiki.set_active("model-1", "coding")
        self.assertEqual(wiki.active_profile("model-1"), "coding")
        wiki.set_active("model-1", "")
        self.assertEqual(wiki.active_profile("model-1"), "")


if __name__ == "__main__":
    unittest.main()
