"""Single-source markdown renderer + content model (pure stdlib, strict subset)."""
import html, os, re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def content_dir():
    import config
    return config.load().get("docs_dir") or os.path.join(_ROOT, "docs", "content")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _slug(text):
    s = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


# ---------- inline spans ----------
_CODE = re.compile(r"`([^`]+)`")
_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITAL = re.compile(r"\*([^*]+)\*")


def _inline(text):
    out = html.escape(text, quote=True)           # escape first (strict/safe)
    codes = []

    def _stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    out = _CODE.sub(_stash, out)                   # protect code spans
    out = _IMG.sub(lambda m: '<img alt="%s" src="%s">' % (m.group(1), m.group(2)), out)
    out = _LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITAL.sub(r"<em>\1</em>", out)
    out = re.sub(r"\x00(\d+)\x00",
                 lambda m: "<code>%s</code>" % codes[int(m.group(1))], out)
    return out


def _render_list(lines, i, n):
    def kind(l):
        if re.match(r"\s*\d+\.\s+", l):
            return "ol"
        if re.match(r"\s*[-*]\s+", l):
            return "ul"
        return None

    def indent(l):
        return len(l) - len(l.lstrip(" "))

    top, base = kind(lines[i]), (len(lines[i]) - len(lines[i].lstrip(" ")))
    items = []
    while i < n and kind(lines[i]) and indent(lines[i]) == base:
        text = re.sub(r"\s*(?:[-*]|\d+\.)\s+", "", lines[i], count=1)
        i += 1
        sub = ""
        if i < n and kind(lines[i]) and indent(lines[i]) > base:
            sub, i = _render_list(lines, i, n)
        items.append("<li>%s%s</li>" % (_inline(text.strip()), sub))
    return "<%s>%s</%s>" % (top, "".join(items), top), i


def render(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out, para, i, n = [], [], 0, len(lines)

    def flush():
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para).strip()))
            para.clear()

    def cells(row):
        return [c.strip() for c in row.strip().strip("|").split("|")]

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            i += 1
            code = []
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            cls = ' class="lang-%s"' % _slug(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape("\n".join(code))))
            continue
        m = re.match(r"(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append('<h%d id="%s">%s</h%d>' % (lvl, _slug(txt), _inline(txt), lvl))
            i += 1
            continue
        if re.match(r"(-{3,}|\*{3,})\s*$", line):
            flush(); out.append("<hr>"); i += 1; continue
        if line.startswith(">"):
            flush()
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i][1:].lstrip()); i += 1
            adm = re.match(r"\[!(NOTE|TIP|WARNING)\]\s*(.*)$", buf[0]) if buf else None
            if adm:
                body = [adm.group(2)] + buf[1:]
                out.append('<div class="admon admon-%s"><p>%s</p></div>'
                           % (adm.group(1).lower(), _inline(" ".join(body).strip())))
            else:
                out.append("<blockquote><p>%s</p></blockquote>"
                           % _inline(" ".join(buf).strip()))
            continue
        if "|" in line and i + 1 < n and re.match(
                r"\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$", lines[i + 1]):
            flush()
            header = cells(line); i += 2
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(cells(lines[i])); i += 1
            th = "".join("<th>%s</th>" % _inline(c) for c in header)
            trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in r)
                          for r in rows)
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                       % (th, trs))
            continue
        if re.match(r"\s*[-*]\s+", line) or re.match(r"\s*\d+\.\s+", line):
            flush()
            html_list, i = _render_list(lines, i, n)
            out.append(html_list)
            continue
        if not line.strip():
            flush(); i += 1; continue
        para.append(line.strip()); i += 1
    flush()
    return "\n".join(out)
