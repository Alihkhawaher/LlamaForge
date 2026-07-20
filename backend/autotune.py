"""Hardware-aware knob recommendations for LlamaForge (pure stdlib).

Turns detected hardware + a GGUF's header facts into a small set of
llama-server knobs, shaped by the user's intent. `recommend` is a pure function
(no I/O) so it is trivially testable; `refine` (Task 4) optionally benchmarks.
Only the ~8 knobs that materially affect fit/throughput are set; everything
else keeps llama.cpp's own defaults.
"""

INTENTS = ("balanced", "speed", "context", "coding")

# Fraction of VRAM the weights may claim, leaving room for the KV cache/activations.
_HEADROOM = {"balanced": 0.90, "speed": 0.92, "context": 0.78, "coding": 0.90}

# Maximum context window for "context" intent.
_CTX_MAX = 150000


def _total_vram_mib(hw):
    return sum((g.get("vram_mib") or 0) for g in hw.get("gpus", []))


def _has_gpu(hw):
    return bool(hw.get("gpus"))


def _fit_ngl(layers, weights_mib, budget_mib):
    """How many layers to offload. '99' = all (llama.cpp caps to the real count)."""
    if not layers or not weights_mib:
        return "99"                      # unknown size: try full offload, refine can back off
    if budget_mib >= weights_mib:
        return "99"
    return str(max(0, int(layers * budget_mib / weights_mib)))


def recommend(meta, hw, intent="balanced", size_bytes=None):
    intent = intent if intent in INTENTS else "balanced"
    knobs, why = {}, {}
    cpu = hw.get("cpu") or {}
    threads = cpu.get("threads") or cpu.get("cores")
    layers = meta.get("block_count")
    weights_mib = (size_bytes / (1024 * 1024)) if size_bytes else None

    if not _has_gpu(hw):
        knobs["n-gpu-layers"] = "0"
        why["n-gpu-layers"] = "No GPU detected - running on CPU."
        knobs["flash-attn"] = "off"
        why["flash-attn"] = "Flash-attention needs a supported GPU."
    else:
        total = _total_vram_mib(hw)
        budget = int(total * _HEADROOM[intent])
        knobs["n-gpu-layers"] = _fit_ngl(layers, weights_mib, budget)
        if knobs["n-gpu-layers"] == "99":
            # Distinguish between unknown size and genuine fit
            if not layers or not weights_mib:
                why["n-gpu-layers"] = "Model size/layer count unknown - attempting full GPU offload."
            else:
                why["n-gpu-layers"] = f"Weights fit in {total} MiB VRAM - full GPU offload."
        else:
            why["n-gpu-layers"] = (f"~{int(weights_mib)} MiB weights vs {budget} MiB budget "
                                   f"- offloading {knobs['n-gpu-layers']}/{layers} layers.")
        knobs["flash-attn"] = "on"
        why["flash-attn"] = "GPU present - flash-attention enabled."

    if threads:
        knobs["threads"] = str(threads)
        why["threads"] = f"Matched to this CPU's {threads} hardware threads."

    # Balanced context: the model's trained length, capped to a sane ceiling.
    trained = meta.get("context_length")
    ctx = _ctx_for(intent, trained)
    if ctx:
        knobs["ctx-size"] = str(ctx)
        why["ctx-size"] = _ctx_reason(intent, trained, ctx)

    # Intent-specific shaping (KV type, batch, tensor-split, sampling) — Task 3.
    _apply_intent(knobs, why, hw, intent)
    return {"knobs": knobs, "rationale": why}


def _ctx_for(intent, trained):
    ceil = {"balanced": 65536, "speed": 16384, "context": _CTX_MAX, "coding": 65536}[intent]
    if not trained or trained <= 0:
        return None
    return min(trained, ceil)


def _ctx_reason(intent, trained, ctx):
    if intent == "context":
        return f"Max-context: using the model's trained {trained} tokens (capped {_CTX_MAX})."
    if intent == "speed":
        return f"Max-speed: smaller {ctx}-token window to cut KV-cache overhead."
    return f"Balanced {ctx}-token window (trained {trained})."


def _apply_intent(knobs, why, hw, intent):
    """Filled in by Task 3. Balanced/CPU need nothing extra."""
    return
