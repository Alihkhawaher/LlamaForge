"""Bundled presets: GPUs (VRAM + memory bandwidth) and popular models (params/active/arch).

Kept deliberately small and hand-verified. Unknown models fall back to the HF fetch (hf.py);
unknown GPUs can be given as raw --vram/--ram numbers. Community PRs extend these tables.
"""
from .physics import Model, Hardware
from . import constants as C

# name -> (vram_gb, mem_bandwidth_GB/s). Aliases collapse to canonical keys.
GPUS = {
    "3060": (12, 360), "3060-8g": (8, 240),
    "3090": (24, 936), "4070": (12, 504), "4070-ti-super": (16, 672),
    "4080": (16, 717), "4090": (24, 1008),
    "5070": (12, 672), "5070-ti": (16, 896), "5080": (16, 960), "5090": (32, 1790),
    "a6000": (48, 768), "a100-40": (40, 1555), "a100-80": (80, 2039),
    # Apple unified memory (VRAM == RAM; pass --ram equal to the model)
    "m1-max": (32, 400), "m2-max": (38, 400), "m3-max": (48, 400),
    "m2-ultra": (76, 800), "m3-ultra": (80, 800),
}
GPU_ALIASES = {
    "rtx3060": "3060", "rtx3090": "3090", "rtx4090": "4090", "rtx4080": "4080",
    "rtx5090": "5090", "rtx5080": "5080", "rtx4070": "4070",
}

# name -> dict(total, active, layers, [aliases]). active==total for dense.
MODELS = {
    "llama-3.1-8b":   dict(total=8e9,   active=8e9,   layers=32),
    "llama-3.1-70b":  dict(total=70e9,  active=70e9,  layers=80),
    "llama-3.1-405b": dict(total=405e9, active=405e9, layers=126),
    "qwen3-32b":      dict(total=32e9,  active=32e9,  layers=64),
    "qwen3-235b-a22b":dict(total=235e9, active=22e9,  layers=94),
    "mistral-7b":     dict(total=7e9,   active=7e9,   layers=32),
    "mixtral-8x7b":   dict(total=47e9,  active=13e9,  layers=32),
    "mixtral-8x22b":  dict(total=141e9, active=39e9,  layers=56),
    "deepseek-r1":    dict(total=671e9, active=37e9,  layers=61),
    "deepseek-v3":    dict(total=671e9, active=37e9,  layers=61),
    "gpt-oss-120b":   dict(total=117e9, active=5.1e9, layers=36),
    "gpt-oss-20b":    dict(total=21e9,  active=3.6e9, layers=24),
    "glm-4.5-air":    dict(total=106e9, active=12e9,  layers=47),
    "glm-4.6":        dict(total=355e9, active=32e9,  layers=92),
    "glm-5.2":        dict(total=754e9, active=7.0e9, layers=92),  # active ~top-4 routed, from measured 3.4GB/tok@3.88bpw
}
MODEL_ALIASES = {
    "llama3-8b": "llama-3.1-8b", "llama-8b": "llama-3.1-8b",
    "llama-70b": "llama-3.1-70b", "llama3-70b": "llama-3.1-70b",
    "r1": "deepseek-r1", "air": "glm-4.5-air", "glm-air": "glm-4.5-air",
}


def resolve_gpu(name: str, ram_gb: float) -> Hardware:
    key = GPU_ALIASES.get(name.lower(), name.lower())
    mult = 1
    if key.endswith("x2"):
        key, mult = key[:-2], 2
    if key not in GPUS:
        raise KeyError(f"unknown GPU '{name}'. Known: {', '.join(sorted(GPUS))}. "
                       f"Or pass --vram <GB> directly.")
    vram, bw = GPUS[key]
    return Hardware(name=name, vram_gb=vram * mult, ram_gb=ram_gb, vram_bw=bw)


def resolve_quant(quant: str) -> float:
    q = quant.lower().replace("-", "_").strip()
    if q in C.QUANT_BPW:
        return C.QUANT_BPW[q]
    # try progressively shorter prefixes (e.g. "q4_k_m_special" -> "q4_k_m" -> "q4")
    for cand in (q, "_".join(q.split("_")[:3]), "_".join(q.split("_")[:2]), q[:2]):
        if cand in C.QUANT_BPW:
            return C.QUANT_BPW[cand]
    raise KeyError(f"unknown quant '{quant}'. Known: {', '.join(sorted(C.QUANT_BPW))}")


def resolve_model(name: str, quant: str) -> Model:
    key = MODEL_ALIASES.get(name.lower(), name.lower())
    if key not in MODELS:
        raise KeyError(f"'{name}' not in the bundled catalog")
    m = MODELS[key]
    return Model(name=name, total_params=m["total"], active_params=m["active"],
                 bpw=resolve_quant(quant), n_layers=m["layers"])
