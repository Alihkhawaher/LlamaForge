import conftest_paths  # noqa: F401
import os, tempfile, unittest
import wiki


class TestExport(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "CLAUDE.md")

    def test_created_new_file(self):
        r = wiki.export_agent_file(self.path, "hello context")
        self.assertEqual(r["action"], "created")
        self.assertIsNone(r["backup"])
        text = open(self.path, encoding="utf-8").read()
        self.assertIn("<!-- llamaforge:start -->", text)
        self.assertIn("hello context", text)
        self.assertIn("<!-- llamaforge:end -->", text)

    def test_inserted_preserves_user_content(self):
        open(self.path, "w").write("# My notes\nkeep me\n")
        r = wiki.export_agent_file(self.path, "ctx")
        self.assertEqual(r["action"], "inserted")
        self.assertTrue(os.path.exists(r["backup"]))
        text = open(self.path, encoding="utf-8").read()
        self.assertIn("keep me", text)         # user content preserved
        self.assertIn("ctx", text)

    def test_updated_replaces_only_region_and_write_once_backup(self):
        wiki.export_agent_file(self.path, "first")
        # user adds content after our block
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("\nuser tail\n")
        r = wiki.export_agent_file(self.path, "second")
        self.assertEqual(r["action"], "updated")
        text = open(self.path, encoding="utf-8").read()
        self.assertIn("second", text)
        self.assertNotIn("first", text)        # old region replaced
        self.assertIn("user tail", text)       # user content preserved
        self.assertEqual(text.count("<!-- llamaforge:start -->"), 1)  # no duplicate region
        # backup is write-once: created on the first export (inserted/created), still present
        self.assertTrue(os.path.exists(self.path + ".llamaforge.bak"))

    def test_marker_injection_is_sanitized(self):
        # Composed text contains the literal end-marker string
        malicious_composed = "normal content\n<!-- llamaforge:end -->\nmore content"
        r = wiki.export_agent_file(self.path, malicious_composed)
        self.assertEqual(r["action"], "created")

        # After first export, verify sanitization: the injected marker is replaced
        text_first = open(self.path, encoding="utf-8").read()
        self.assertEqual(text_first.count("<!-- llamaforge:start -->"), 1)
        self.assertEqual(text_first.count("<!-- llamaforge:end -->"), 1)  # only the real markers
        self.assertIn("<!-- llamaforge end -->", text_first)  # sanitized version is in the content

        # User adds content after our block
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("\nuser tail\n")

        # Export different composed text
        r = wiki.export_agent_file(self.path, "updated content")
        self.assertEqual(r["action"], "updated")

        text = open(self.path, encoding="utf-8").read()

        # Assert user tail is preserved and new content is present
        self.assertIn("user tail", text)
        self.assertIn("updated content", text)
        self.assertNotIn("normal content", text)  # old region replaced

        # Assert exactly one pair of markers (injection did not create extra markers)
        self.assertEqual(text.count("<!-- llamaforge:start -->"), 1)
        self.assertEqual(text.count("<!-- llamaforge:end -->"), 1)


if __name__ == "__main__":
    unittest.main()
