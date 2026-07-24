---
title: Connect an Agent
section: guides
order: 8
---

# Connect an Agent

Point a coding agent — Claude Code, Codex, or pi.dev — at your locally loaded models with one click, using either the Anthropic-compatible shim or the OpenAI-compatible router directly.

## What it does

LlamaForge exposes two HTTP surfaces a coding agent can talk to:

- The **router** (`router_port`, default 8080) speaks the OpenAI `/v1/chat/completions` shape natively — this is what llama.cpp's router already serves.
- The **Anthropic shim** (`backend/anthropic_shim.py`, served from the panel on `panel_port`, default 8090) translates Anthropic's `/v1/messages` Messages API into the router's OpenAI request shape and back, including streaming SSE and tool use, so an Anthropic-API client like Claude Code can drive a local model without knowing it isn't talking to Anthropic. `to_openai_request()` maps system/messages/tools/tool_choice/stop_sequences into the OpenAI body; `to_anthropic_response()` and `stream_anthropic_events()` map the router's response (or SSE chunk stream) back into Anthropic message/content-block events. `/v1/messages/count_tokens` is served too, but only as an estimate (`count_tokens_estimate()`: ~4 characters per token over the translated prompt text, not a real tokenizer count).

Shim auth (`backend/server.py` `_shim_auth_ok()`) accepts either header an Anthropic client might send: `x-api-key: <key>` or `Authorization: Bearer <key>`. If the router is bound to `127.0.0.1` (the default), auth is skipped entirely; it's only enforced once `router_host` is changed to something reachable off the local machine, and only if a `router_api_key` is actually set — an empty key also skips the check.

**Agent setup** (`backend/agentsetup.py`) generates the config each agent needs to point at LlamaForge, and can optionally write it in place:

| Agent | Config file | Format | Endpoint it's given |
|---|---|---|---|
| `claude-code` | `~/.claude/settings.json` | JSON (`env` block) | The Anthropic shim, `http://127.0.0.1:<panel_port>` — always localhost, never the LAN, because the shim only binds locally. |
| `codex` | `~/.codex/config.toml` | TOML (appended provider block) | The router's OpenAI-compatible endpoint, `http://<host>:<router_port>/v1` — `<host>` is the LAN IP when `router_host` is non-local, else `127.0.0.1`. |
| `pi` | `~/.pi/agent/models.json` | JSON (`providers` block) | Same router endpoint rule as Codex. |

Claude Code's generated `settings.json` sets `ANTHROPIC_BASE_URL` to the shim endpoint, `ANTHROPIC_AUTH_TOKEN` to the router API key (or the literal string `llamaforge` if none is set — the shim needs a non-empty token even when auth is effectively open), `ANTHROPIC_MODEL`, and `ANTHROPIC_SMALL_FAST_MODEL`. Codex's TOML block declares a `[model_providers.llamaforge]` section with `wire_api = "chat"` and, if a router API key exists, an `env_key` pointing at a `LLAMAFORGE_API_KEY` environment variable the user must set — the key itself is never written to the TOML file. pi's `models.json` sets `api: "openai-completions"` with the key embedded directly in the config.

Codex and pi can optionally be routed through the shim instead of the router directly by passing `inject=true` — this is how those two agents pick up wiki context injection (see [Context Wiki](context-wiki.md)), since only requests through the shim/proxy get the composed system-prompt merge.

Two apply paths exist: `generate()` returns the config content and a human-readable target path/instructions without touching disk (used for "copy this into your config" display); `apply()` actually writes it — JSON targets are deep-merged into any existing file (`_deep_merge()`, so unrelated existing keys survive), and the Codex TOML target is appended only if the `[model_providers.llamaforge]` block isn't already present, commenting out any conflicting top-level `model`/`model_provider` line rather than deleting it. Both paths back up the target file once, to `<path>.llamaforge.bak`, before the first write.

## How to use it

1. Open the **Setup** tab and pick the agent you want to connect: Claude Code, Codex, or pi.dev.
2. Choose the model (and, for Claude Code, an optional small/fast model) it should use.
3. Preview the generated config and endpoint. For Codex or pi.dev, optionally enable context injection to route through the shim instead of the router directly.
4. Click **Apply** to write the config into the agent's real config file on this machine, or copy the generated snippet and merge it yourself.
5. Launch the agent. Claude Code must run on the same machine as LlamaForge — its endpoint is always `127.0.0.1`.

## Reference

| Concept | Source | Behavior |
|---|---|---|
| Anthropic request translation | `backend/anthropic_shim.py` `to_openai_request()` | Anthropic Messages body -> OpenAI chat body (system, messages incl. tool_use/tool_result, tools, tool_choice, stop_sequences). |
| Anthropic response translation | `backend/anthropic_shim.py` `to_anthropic_response()` / `stream_anthropic_events()` | OpenAI response/SSE -> Anthropic message / streaming content-block events. |
| Token estimate | `backend/anthropic_shim.py` `count_tokens_estimate()` | Advisory only: `len(text) // 4` over the translated prompt. |
| Shim auth | `backend/server.py` `_shim_auth_ok()` | Accepts `x-api-key` or `Authorization: Bearer <key>`; skipped when `router_host` is `127.0.0.1` or no `router_api_key` is set. |
| Endpoint per agent | `backend/server.py` `_agent_endpoint()` | Claude Code -> shim at `127.0.0.1:panel_port`; Codex/pi -> router at `<host>:router_port/v1`. |
| Config generation | `backend/agentsetup.py` `generate()` | Pure: returns `{agent, format, target_path, content, endpoint, instructions}` without writing. |
| Config apply | `backend/agentsetup.py` `apply()` | Writes to the real target path; JSON deep-merged, Codex TOML appended if absent; backs up the original once. |

## Troubleshooting

If Claude Code can't reach LlamaForge, confirm it's running on the same machine — the shim endpoint is hardcoded to `127.0.0.1` and never the LAN IP, by design (`_agent_endpoint()`: "shim binds localhost only"). If Codex or pi.dev requests fail auth after changing `router_host`, make sure `LLAMAFORGE_API_KEY` (Codex) or the embedded `apiKey` (pi) actually matches the current `router_api_key` in config — a stale key set before you edited config will keep failing. If re-applying a config seems to have no effect, check `<path>.llamaforge.bak` next to the target file: it holds the original from before LlamaForge ever touched it, since the backup is only ever written once.

See also [Context Wiki](context-wiki.md) for how injected context reaches requests that go through the shim or router proxy.
