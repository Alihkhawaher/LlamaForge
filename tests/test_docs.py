import conftest_paths  # noqa: F401
import unittest
import docs


class TestRenderInline(unittest.TestCase):
    def test_heading_with_id(self):
        self.assertEqual(docs.render("# Hello World"),
                         '<h1 id="hello-world">Hello World</h1>')

    def test_paragraph_and_spans(self):
        html = docs.render("A **bold** and *italic* and `code` and [t](u).")
        self.assertEqual(
            html,
            '<p>A <strong>bold</strong> and <em>italic</em> and '
            '<code>code</code> and <a href="u">t</a>.</p>')

    def test_image(self):
        self.assertEqual(docs.render("![alt](docs/img/x.png)"),
                         '<p><img alt="alt" src="docs/img/x.png"></p>')

    def test_hr(self):
        self.assertEqual(docs.render("---"), "<hr>")

    def test_raw_html_is_escaped(self):
        self.assertEqual(docs.render("<script>x</script>"),
                         "<p>&lt;script&gt;x&lt;/script&gt;</p>")

    def test_code_span_content_escaped(self):
        self.assertEqual(docs.render("`<b>`"), "<p><code>&lt;b&gt;</code></p>")


if __name__ == "__main__":
    unittest.main()
