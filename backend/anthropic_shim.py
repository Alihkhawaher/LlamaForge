"""Anthropic <-> OpenAI translation for LlamaForge's /v1/messages shim.

Pure-stdlib, pure functions over dicts (no I/O): backend/server.py orchestrates
the actual router calls. Translates Anthropic Messages API requests to the
router's OpenAI chat-completions shape and back, including streaming SSE and
tool use, so Claude Code can drive local llama.cpp models.
"""
import json
import uuid


# ---------------- request: Anthropic -> OpenAI ----------------

def _collapse(parts):
    """A list of OpenAI content parts -> a plain string when all are text,
    else the parts list (needed for image content)."""
    if all(p.get("type") == "text" for p in parts):
        return "".join(p.get("text", "") for p in parts)
    return parts


def content_blocks_to_openai(role, content):
    """Translate one Anthropic message's content into OpenAI messages.
    Usually one message, but tool_result blocks become separate role=tool
    messages, and an assistant turn with tool_use becomes one assistant message
    carrying tool_calls."""
    if isinstance(content, str):
        return [{"role": role, "content": content}]
    text_parts, tool_calls, tool_msgs = [], [], []
    for b in content or []:
        t = b.get("type")
        if t == "text":
            text_parts.append({"type": "text", "text": b.get("text", "")})
        elif t == "image":
            src = b.get("source", {})
            if src.get("type") == "base64":
                url = f"data:{src.get('media_type', 'image/png')};base64,{src.get('data', '')}"
                text_parts.append({"type": "image_url", "image_url": {"url": url}})
        elif t == "tool_use":
            tool_calls.append({"id": b.get("id"), "type": "function", "function": {
                "name": b.get("name"), "arguments": json.dumps(b.get("input", {}))}})
        elif t == "tool_result":
            c = b.get("content")
            if isinstance(c, list):
                c = "".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
            tool_msgs.append({"role": "tool", "tool_call_id": b.get("tool_use_id"),
                              "content": c if isinstance(c, str) else json.dumps(c)})
    out = []
    if role == "assistant" and tool_calls:
        msg = {"role": "assistant", "content": _collapse(text_parts) if text_parts else None,
               "tool_calls": tool_calls}
        out.append(msg)
    elif text_parts:
        out.append({"role": role, "content": _collapse(text_parts)})
    out.extend(tool_msgs)
    return out


def map_tools(tools):
    out = []
    for t in tools or []:
        out.append({"type": "function", "function": {
            "name": t.get("name"), "description": t.get("description", ""),
            "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}})
    return out


def map_tool_choice(tc):
    if isinstance(tc, dict):
        ty = tc.get("type")
        if ty == "auto":
            return "auto"
        if ty == "any":
            return "required"
        if ty == "tool" and tc.get("name"):
            return {"type": "function", "function": {"name": tc["name"]}}
    return "auto"


def to_openai_request(a):
    out = {"model": a.get("model", "")}
    msgs = []
    system = a.get("system")
    if isinstance(system, str) and system:
        msgs.append({"role": "system", "content": system})
    elif isinstance(system, list):
        text = "".join(b.get("text", "") for b in system if b.get("type") == "text")
        if text:
            msgs.append({"role": "system", "content": text})
    for m in a.get("messages", []):
        msgs.extend(content_blocks_to_openai(m.get("role"), m.get("content")))
    out["messages"] = msgs
    if "max_tokens" in a:
        out["max_tokens"] = a["max_tokens"]
    if "temperature" in a:
        out["temperature"] = a["temperature"]
    if "top_p" in a:
        out["top_p"] = a["top_p"]
    if a.get("stop_sequences"):
        out["stop"] = a["stop_sequences"]
    if a.get("stream"):
        out["stream"] = True
    if a.get("tools"):
        out["tools"] = map_tools(a["tools"])
    if a.get("tool_choice") is not None:
        out["tool_choice"] = map_tool_choice(a["tool_choice"])
    return out
