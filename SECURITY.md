# Security

## Default: local only

By default, both processes bind to `127.0.0.1` and are not reachable from
your network:

- The LlamaForge dashboard (`backend/server.py`), on `panel_port` (default 8090).
- The llama.cpp router (`llama-server.exe --models-preset ...`), on `router_port`
  (default 8080).

## Opt-in: LAN access for the router

The Setup tab's **Network Access** panel lets you switch the llama.cpp
router's bind address from `127.0.0.1` to `0.0.0.0`, making it reachable from
other devices on your network (e.g. to use the chat UI from your phone, or
point another machine's OpenAI-compatible client at it).

When enabled:

- An **API key is strongly recommended**. A **Require an API key** toggle
  (on by default) makes the panel refuse to enable LAN access until you set
  or generate one; the panel can generate a random key for you. If you
  uncheck the toggle and leave the key blank, the router is served to your
  network **unauthenticated** - anyone who can reach the port can use it.
  When a key is set, clients must send `Authorization: Bearer <key>`.
- `GET /models` (a metadata listing, no prompts or completions) is not
  covered by the key - this is llama.cpp's own behavior, not
  LlamaForge-specific. All inference endpoints (`/completion`,
  `/v1/chat/completions`, etc.) are.
- The setting is saved in `config.json` and re-applied on every restart
  (including autostart), so it persists until you turn it back off.
- Windows Firewall must allow inbound connections to `llama-server.exe` on
  your network profile; if you're prompted by Windows the first time, allow
  it for the profile you're actually on (Private/Public).

The **LlamaForge dashboard itself** (port 8090) always stays local-only -
it can trigger rebuilds, install prerequisites, and edit configuration, so
it is intentionally not exposed by this feature. If you need to administer
LlamaForge from another device, use remote desktop / SSH to this machine
rather than exposing port 8090.

## Threat model for the dashboard

Binding to `127.0.0.1` keeps the dashboard off your network, but it does **not**
put it out of reach: every web page you visit can send requests to
`http://127.0.0.1:8090`. Since the dashboard's routes rebuild llama.cpp, install
packages, run commands inside WSL and rewrite configuration, a page you merely
*visit* must not be able to drive it.

So the treated-as-untrusted input is **any HTTP request**, including one from
your own browser, and the following rules apply:

- **Origin and Host are checked on every request.** A request whose `Origin`
  names another site is refused (403), as is one whose `Host` is not this
  loopback service - the latter blocks DNS rebinding, where an attacker's
  hostname is re-pointed at `127.0.0.1` so their page counts as same-origin.
- **State-changing requests must be `application/json`.** A cross-site
  `<form>` can only send `text/plain`, `application/x-www-form-urlencoded` or
  `multipart/form-data`; requiring JSON means a forged POST needs a CORS
  preflight it cannot pass. Requests with a form content type get a 415.
- **`POST /api/config` accepts an allowlist of keys**, each type-checked. Keys
  naming a program or directory the backend reads (`server_bin`, `llama_src`,
  `build_dir`, `models_ini`, `wiki_dir`, `docs_dir`) are *not* settable from the
  browser - `server_bin` in particular is executed as `<server_bin> --help` to
  build the knob schema. Those belong to `bootstrap` and `config.json`.
- **Nothing from a request is interpolated into a shell command.** vLLM runs
  through `bash -lc` inside WSL; model refs, HF repo ids and knob values are
  bound as positional parameters (`"$1"`), and repo ids are additionally
  validated against `org/name`. See the module docstring in `backend/wsl.py`.

The router's API key is included in `/api/state` so the *Client config* panel can
show a working `curl`. That is same-origin data on a loopback-only service; it is
not a secret from the page that is already the dashboard.

## Reporting

This is a personal/local tool, not a hosted service. If you find a security
issue, please open an issue on the repo.
