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
    c = config.load()
    profs = c.get("wiki_profiles")
    if not isinstance(profs, dict):
        profs = {}
    profs[name] = {"docs": [_safe_name(x) for x in (docs or [])],
                   "description": description or ""}
    c["wiki_profiles"] = profs
    config.save(c)
    return profs


def delete_profile(name):
    c = config.load()
    profs = c.get("wiki_profiles")
    if isinstance(profs, dict) and name in profs:
        del profs[name]
        c["wiki_profiles"] = profs
        config.save(c)
        return True
    return False


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
    c = config.load()
    a = c.get("wiki_active")
    if not isinstance(a, dict):
        a = {}
    if profile:
        a[model_id] = profile
    elif model_id in a:
        del a[model_id]
    c["wiki_active"] = a
    config.save(c)
