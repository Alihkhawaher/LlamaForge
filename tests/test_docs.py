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

    def test_quote_in_image_alt_escaped(self):
        html = docs.render('![x"onerror="alert(1)](u)')
        self.assertNotIn('"onerror="', html)      # quote cannot break out of the attribute

    def test_quote_in_link_escaped(self):
        html = docs.render('[t"x](u)')
        self.assertNotIn('t"x', html)


class TestRenderBlocks(unittest.TestCase):
    def test_fenced_code_with_lang(self):
        self.assertEqual(docs.render("```bash\nls -la\n```"),
                         '<pre><code class="lang-bash">ls -la</code></pre>')

    def test_fenced_code_escaped(self):
        self.assertEqual(docs.render("```\n<a>\n```"),
                         "<pre><code>&lt;a&gt;</code></pre>")

    def test_unordered_list(self):
        self.assertEqual(docs.render("- one\n- two"),
                         "<ul><li>one</li><li>two</li></ul>")

    def test_ordered_list(self):
        self.assertEqual(docs.render("1. a\n2. b"),
                         "<ol><li>a</li><li>b</li></ol>")

    def test_nested_list(self):
        self.assertEqual(docs.render("- a\n  - b"),
                         "<ul><li>a<ul><li>b</li></ul></li></ul>")

    def test_table(self):
        self.assertEqual(
            docs.render("| A | B |\n| --- | --- |\n| 1 | 2 |"),
            "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
            "<tbody><tr><td>1</td><td>2</td></tr></tbody></table>")

    def test_blockquote(self):
        self.assertEqual(docs.render("> quoted"),
                         "<blockquote><p>quoted</p></blockquote>")

    def test_admonition(self):
        self.assertEqual(docs.render("> [!NOTE] heads up"),
                         '<div class="admon admon-note"><p>heads up</p></div>')


if __name__ == "__main__":
    unittest.main()
