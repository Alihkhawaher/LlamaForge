"""Context wiki: a working directory of markdown docs, composed into named
profiles selected per model, for injection (proxy) or export (agent files).

Pure stdlib. compose(active_profile(model_id)) is the single value both
delivery paths consume. Doc names are sanitized so they never escape wiki_dir.
"""
import os
import shutil

import config


def _dir():
    return config.load().get("wiki_dir") or os.path.join(config.ROOT, "wiki")


def _safe_name(name):
    base = (name or "").strip()
    if not base or "/" in base or "\\" in base:
        raise ValueError("invalid doc name")
    base = os.path.basename(base)
    if base in (".", ".."):
        raise ValueError("invalid doc name")
    if not base.endswith(".md"):
        base += ".md"
    return base


def list_docs():
    d = _dir()
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d)
                  if f.endswith(".md") and os.path.isfile(os.path.join(d, f)))


def read_doc(name):
    try:
        with open(os.path.join(_dir(), _safe_name(name)), encoding="utf-8-sig") as f:
            return f.read()
    except (OSError, ValueError):
        return ""


def write_doc(name, text):
    safe = _safe_name(name)          # raises before any write on a bad name
    d = _dir()
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, safe), "w", encoding="utf-8", newline="") as f:
        f.write(text or "")


def delete_doc(name):
    p = os.path.join(_dir(), _safe_name(name))
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


def get_profiles():
    p = config.load().get("wiki_profiles")
    return p if isinstance(p, dict) else {}


def save_profile(name, docs, description=""):
    name = (name or "").strip()
    if not name:
        raise ValueError("profile name is required")
    entry = {"docs": [_safe_name(x) for x in (docs or [])],
             "description": description or ""}   # validate before taking the lock

    def _apply(c):
        profs = c.get("wiki_profiles")
        if not isinstance(profs, dict):
            profs = {}
        profs[name] = entry
        c["wiki_profiles"] = profs
        return profs
    return config.mutate(_apply)


def delete_profile(name):
    def _apply(c):
        profs = c.get("wiki_profiles")
        if isinstance(profs, dict) and name in profs:
            del profs[name]
            c["wiki_profiles"] = profs
            return True
        return False
    return config.mutate(_apply)


def compose(profile_name):
    if not profile_name:
        return ""
    prof = get_profiles().get(profile_name)
    if not prof:
        return ""
    parts = []
    for doc in prof.get("docs", []):
        text = read_doc(doc)
        if text.strip():
            title = doc[:-3] if doc.endswith(".md") else doc
            parts.append(f"## {title}\n\n{text.strip()}")
    return "\n\n".join(parts)


def active_profile(model_id):
    a = config.load().get("wiki_active")
    return (a.get(model_id) if isinstance(a, dict) else "") or ""


def set_active(model_id, profile):
    def _apply(c):
        a = c.get("wiki_active")
        if not isinstance(a, dict):
            a = {}
        if profile:
            a[model_id] = profile
        elif model_id in a:
            del a[model_id]
        c["wiki_active"] = a
    config.mutate(_apply)


# ---------------- delivery A: agent-file export ----------------

_MARK_START = "<!-- llamaforge:start -->"
_MARK_END = "<!-- llamaforge:end -->"


def _sanitize(composed):
    return (composed or "").replace(_MARK_START, "<!-- llamaforge start -->").replace(_MARK_END, "<!-- llamaforge end -->")


def _backup(path):
    if os.path.exists(path):
        bak = path + ".llamaforge.bak"
        if not os.path.exists(bak):          # write-once: preserve the true original
            shutil.copy2(path, bak)
        return bak
    return None


def export_agent_file(path, composed):
    region = f"{_MARK_START}\n{_sanitize(composed).strip()}\n{_MARK_END}\n"
    existed = os.path.exists(path)
    backup = _backup(path)
    text = ""
    if existed:
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    if _MARK_START in text and _MARK_END in text:
        pre = text.split(_MARK_START, 1)[0]
        post = text[text.rindex(_MARK_END) + len(_MARK_END):].lstrip("\n")
        new = pre + region + post
        action = "updated"
    else:
        sep = "\n" if (text and not text.endswith("\n")) else ""
        gap = "\n" if text else ""
        new = text + sep + gap + region
        action = "inserted" if existed else "created"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    return {"ok": True, "path": path, "backup": backup, "action": action}
