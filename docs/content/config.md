---
title: config.json Reference
section: reference
order: 1
---

# config.json Reference

`config.json` lives at the repository root and holds every machine-specific setting LlamaForge needs — nothing is hardcoded into the source. It is created by the bootstrap scripts on first run and updated by the dashboard (`POST /api/config`, `POST /api/network`) as you use it. `backend/config.py` defines the defaults; any key missing from the file on disk falls back to its default at load time.

## Keys

| Key | Type | Default | Meaning |
|---|---|---|---|
| `llama_src` | string | `""` | Path to a git checkout of `llama.cpp`. |
| `build_dir` | string | `""` | CMake build directory for `llama.cpp` (usually `<llama_src>/build`). |
| `server_bin` | string | `""` | Path to the built `llama-server` (or `llama-server.exe`) binary. |
| `models_ini` | string | `<repo root>/models.ini` | Path to the `models.ini` preset file passed to `llama-server --models-preset`. |
| `model_dirs` | list | `[]` | Directories the Discover/scan feature searches for GGUF files. |
| `router_port` | int | `8080` | Port `llama-server` (the router) listens on. |
| `panel_port` | int | `8090` | Port the LlamaForge dashboard (`backend/server.py`) listens on. |
| `router_host` | string | `"127.0.0.1"` | Router bind address. `127.0.0.1` = local only; `0.0.0.0` = reachable on the LAN. |
| `router_api_key` | string | `""` | API key required from clients when `router_host` is not `127.0.0.1`. |
| `wsl_distro` | string | `""` | WSL distro that runs vLLM. Empty string auto-picks the default distro. |
| `vllm_port` | int | `8081` | Port vLLM serves on inside WSL (localhost-forwarded to Windows). |
| `cmake_flags` | object | `{}` | Persisted CMake build flags, normally seeded from hardware detection. |
| `git_remote` | string | `"https://github.com/ggml-org/llama.cpp"` | Remote used to clone/update the `llama.cpp` source. |
| `auto_load_model` | string | `""` | Model id to load automatically on launch. Empty string disables auto-load. |
| `presets` | object | `{}` | Named knob sets: `{name: {knob: value}}`, managed from the dashboard. |
| `ui_mode` | string | `"lite"` | `"lite"` shows a curated knob set; `"advanced"` exposes all ~220 llama-server flags. |
| `onboarded` | bool | `False` | Whether the first-run wizard has already been shown; set to `True` once dismissed. |
| `anthropic_default_model` | string | `""` | Fallback local model id used by the Anthropic-compatible shim when a request doesn't map to one. |
| `anthropic_shim_enabled` | bool | `True` | Whether `/v1/messages` (Anthropic-compatible) is served. |
| `wiki_dir` | string | `""` | Context-doc directory for the wiki feature. Empty string resolves to `<repo root>/wiki`. |
| `wiki_profiles` | object | `{}` | Named context-doc profiles: `{name: {"docs": [...], "description": str}}`. |
| `wiki_active` | object | `{}` | Active profile per model: `{model_id: profile_name}`. |
| `theme` | string | `""` | UI theme. Empty string follows OS/`localStorage`; otherwise `"light"` or `"dark"`. |
| `cvd` | bool | `False` | Enables the colorblind-safe palette and non-color status cues. |
| `docs_dir` | string | `""` | Directory the in-app docs viewer reads from. Empty string resolves to `<repo root>/docs/content`. |

25 keys total, matching `DEFAULTS` in `backend/config.py`.

## Loading and saving

`config.load()` deep-copies `DEFAULTS` and overlays whatever is present in `config.json` on disk, so a config file written before a new key was added still works — the new key simply falls back to its default. `config.save()` writes the full in-memory dict back to disk as indented JSON.

`config.migrate()` runs once at server startup (`backend/server.py` `main()`) to classify pre-existing installs: a config file with no `ui_mode` key is treated as a legacy install. If `server_bin` is already set, it is stamped `ui_mode: "advanced"` and `onboarded: True`; otherwise it gets `ui_mode: "lite"` and `onboarded: False`, so the onboarding wizard shows. The migration is idempotent — a config that already has `ui_mode` is returned unchanged.

See also [models.ini Format](models-ini.md) for the preset file `models_ini` points at, and [HTTP API](api.md) for the endpoints that read and write these keys.
