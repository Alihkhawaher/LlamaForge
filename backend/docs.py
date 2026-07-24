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


def render(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out, para, i, n = [], [], 0, len(lines)

    def flush():
        if para:
            out.append("<p>%s</p>" % _inline(" ".join(para).strip()))
            para.clear()

    while i < n:
        line = lines[i]
        m = re.match(r"(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append('<h%d id="%s">%s</h%d>' % (lvl, _slug(txt), _inline(txt), lvl))
            i += 1
            continue
        if re.match(r"(-{3,}|\*{3,})\s*$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)
