"""Generate (and optionally apply) coding-agent config for LlamaForge endpoints.

Claude Code talks to the Anthropic shim (panel port); Codex and pi.dev talk to
the OpenAI-compatible router (router port /v1). Generators are pure (inputs ->
config content); apply() performs file I/O. Pure stdlib: JSON configs are
deep-merged; Codex TOML is append-if-absent (no stdlib TOML writer exists).
"""
import copy
import json
import os
import re
import shutil

AGENTS = ("claude-code", "codex", "pi")
PROVIDER = "llamaforge"

_PATHS = {
    "claude-code": ".claude/settings.json",
    "codex": ".codex/config.toml",
    "pi": ".pi/agent/models.json",
}


def _display_path(agent):
    return "~/" + _PATHS[agent]


# ---------------- generators (pure) ----------------

def _gen_claude(endpoint, api_key, model, small_model):
    settings = {"env": {
        "ANTHROPIC_BASE_URL": endpoint,
        "ANTHROPIC_AUTH_TOKEN": api_key or "llamaforge",
        "ANTHROPIC_MODEL": model,
        "ANTHROPIC_SMALL_FAST_MODEL": small_model,
    }}
    return {
        "agent": "claude-code", "format": "json",
        "target_path": _display_path("claude-code"),
        "content": json.dumps(settings, indent=2),
        "endpoint": endpoint,
        "instructions": ("Merge this into ~/.claude/settings.json, or export the "
                         "same keys as environment variables before running Claude Code."),
    }


def _codex_provider_block(endpoint, api_key):
    lines = [f"[model_providers.{PROVIDER}]", 'name = "LlamaForge"',
             f'base_url = "{endpoint}"', 'wire_api = "chat"']
    if api_key:
        lines.append('env_key = "LLAMAFORGE_API_KEY"')
    return "\n".join(lines) + "\n"


def _codex_top_level(model):
    return [f'model = "{model}"', f'model_provider = "{PROVIDER}"']


def _gen_codex(endpoint, api_key, model):
    content = _codex_provider_block(endpoint, api_key) + "\n" + "\n".join(_codex_top_level(model)) + "\n"
    instr = "Add this to ~/.codex/config.toml."
    if api_key:
        instr += " Set LLAMAFORGE_API_KEY in your environment to your router API key."
    return {"agent": "codex", "format": "toml", "target_path": _display_path("codex"),
            "content": content, "endpoint": endpoint, "instructions": instr}


def _gen_pi(endpoint, api_key, model):
    cfg = {"providers": {PROVIDER: {
        "baseUrl": endpoint, "api": "openai-completions",
        "apiKey": api_key or "llamaforge", "models": [{"id": model}]}}}
    return {"agent": "pi", "format": "json", "target_path": _display_path("pi"),
            "content": json.dumps(cfg, indent=2), "endpoint": endpoint,
            "instructions": "Merge this into ~/.pi/agent/models.json."}


def generate(agent, endpoint, api_key, model, small_model=None):
    if agent == "claude-code":
        return _gen_claude(endpoint, api_key, model, small_model or model)
    if agent == "codex":
        return _gen_codex(endpoint, api_key, model)
    if agent == "pi":
        return _gen_pi(endpoint, api_key, model)
    raise ValueError(f"unknown agent: {agent}")
