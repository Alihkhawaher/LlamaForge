"""Single choke point for everything WSL2. vLLM is Linux-only, so LlamaForge
drives it through `wsl.exe`. Centralizing here means the rest of the backend
never spells out wsl.exe, and tests mock exactly one module.

Injection safety
----------------
Commands run under `bash -lc`, so anything interpolated into the script text is
executed as shell syntax. Model ids, HF repo names and vLLM knob values all
originate from HTTP request bodies, and a value like `x; rm -rf ~` used to run
verbatim.

So run()/popen() take a *trusted literal script* plus untrusted `args`, which
are passed to bash as positional parameters and referenced as "$1", "$2",
"$@". Data never becomes syntax:

    wsl.run('rm -rf "$HOME/.cache/huggingface/hub/$1"', cache_dirname)

Callers must never build the script by f-stringing request data into it. For
config-supplied POSIX paths (the venv, the HF cache root) use sh_path(), which
quotes them and expands a leading `~`.

Windows-only. No third-party deps.
"""
import re, shlex, subprocess

CREATE_NO_WINDOW = 0x08000000


def win_to_wsl(path):
    """C:\\a\\b or C:/a/b -> /mnt/c/a/b. Leaves already-POSIX paths alone."""
    p = path.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)$", p)
    if m:
        return f"/mnt/{m.group(1).lower()}/{m.group(2)}"
    return p


def _run_text(args, timeout=15):
    """Run a wsl.exe management command and return decoded stdout.
    `wsl -l -v` emits UTF-16-LE; decode leniently and strip NULs."""
    out = subprocess.run(args, capture_output=True, timeout=timeout,
                         creationflags=CREATE_NO_WINDOW).stdout
    try:
        text = out.decode("utf-16-le")
    except Exception:
        text = out.decode("utf-8", errors="replace")
    return text.replace("\x00", "")


def list_distros():
    """[{name, state, version, default}] or [] if WSL isn't installed."""
    try:
        text = _run_text(["wsl.exe", "-l", "-v"])
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return []
    distros = []
    for line in text.splitlines()[1:]:            # skip the header row
        s = line.rstrip()
        if not s.strip():
            continue
        default = s.lstrip().startswith("*")
        parts = s.replace("*", " ", 1).split()
        if len(parts) >= 3:
            distros.append({"name": parts[0], "state": parts[1],
                            "version": parts[2], "default": default})
    return distros


def default_distro():
    for d in list_distros():
        if d["default"]:
            return d["name"]
    ds = list_distros()
    return ds[0]["name"] if ds else ""


def sh_path(p):
    """Quote a config-supplied POSIX path for embedding in a script.

    A leading `~` becomes "$HOME" (which expands inside double quotes, unlike a
    quoted tilde) and the remainder is shell-quoted. Use this for paths that
    come from config.json; use a positional parameter for anything from an HTTP
    request."""
    p = (p or "").strip()
    if p == "~" or p.startswith("~/"):
        return '"$HOME"' + shlex.quote(p[1:]) if len(p) > 1 else '"$HOME"'
    return shlex.quote(p)


def _argv(script, args, distro):
    """wsl.exe argv for `script` with `args` bound to $1..$n.

    `bash -lc SCRIPT NAME ARG...` sets $0=NAME and $1.. to ARG..., so untrusted
    values arrive as data the script references, never as text bash parses."""
    argv = ["wsl.exe"]
    if distro:
        argv += ["-d", distro]
    argv += ["--", "bash", "-lc", script, "bash"]
    argv += [str(a) for a in args]
    return argv


def run(script, *args, distro=None, timeout=60):
    """Run a shell script inside the distro. Returns (returncode, stdout, stderr).
    Uses `bash -lc` so the login environment (PATH from ~/.profile) is present.
    `script` must be a literal; pass request-derived values via `args`."""
    r = subprocess.run(_argv(script, args, distro), capture_output=True,
                       text=True, timeout=timeout,
                       creationflags=CREATE_NO_WINDOW)
    return r.returncode, r.stdout, r.stderr


def popen(script, *args, stdout, stderr, distro=None):
    """Long-running command (a server or an install). Caller supplies open file
    objects for stdout/stderr; returns the Popen handle. Same script/args
    contract as run()."""
    return subprocess.Popen(_argv(script, args, distro), stdout=stdout,
                            stderr=stderr, stdin=subprocess.DEVNULL,
                            creationflags=CREATE_NO_WINDOW, close_fds=True)
