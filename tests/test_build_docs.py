# tests/test_build_docs.py
import conftest_paths  # noqa: F401
import os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import docs
import build_docs


class TestBuildDocs(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.src, "img"))
        for name, sec in [("intro", "getting-started"), ("models", "guides")]:
            with open(os.path.join(self.src, name + ".md"), "w", encoding="utf-8") as f:
                f.write("---\ntitle: %s\nsection: %s\norder: 1\n---\n# %s\ntext" % (name, sec, name))
        with open(os.path.join(self.src, "_style.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: S\nsection: guides\norder: 0\n---\nx")
        open(os.path.join(self.src, "img", "a.png"), "wb").write(b"\x89PNG")
        self._orig = docs.content_dir
        docs.content_dir = lambda: self.src
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        docs.content_dir = self._orig

    def test_build_emits_pages_and_copies_images_skips_underscore(self):
        written = build_docs.build(self.out)
        self.assertTrue(os.path.exists(os.path.join(self.out, "intro.html")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "models.html")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "docs", "img", "a.png")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "_style.html")))
        body = open(os.path.join(self.out, "intro.html"), encoding="utf-8").read()
        self.assertIn("<h1", body)
        self.assertIn("LlamaForge", body)  # template chrome present


if __name__ == "__main__":
    unittest.main()
