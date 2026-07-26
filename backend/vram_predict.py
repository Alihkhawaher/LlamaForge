"""LlamaForge-owned adapter over the vendored vramwise physics core.

The ONLY module that imports backend/vramwise/. Maps LlamaForge's data sources
(hardware detection, GGUF metadata, HuggingFace config.json, config bandwidth
overrides) onto vramwise's Model/Hardware dataclasses, runs predict(), and
returns a normalized dict. Never raises into the request path: any missing
input degrades to a lower-confidence result with a plain-language note.
"""
import json, os, re, threading, urllib.request

import config, hardware, gguf
from vramwise import physics, catalog, constants as C

HF = "https://huggingface.co"
UA = {"User-Agent": "LlamaForge/1.0 (+local model manager)"}

_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CFG_CACHE = {}            # repo -> config.json dict (one network call per repo)


def _preset_vram_bw(name):
    """Detected nvidia-smi GPU name -> catalog VRAM bandwidth (GB/s); default if unknown."""
    n = (name or "").lower()
    for junk in ("nvidia", "geforce", "rtx", "gtx", " "):
        n = n.replace(junk, "")
    for key, (_vram, bw) in catalog.GPUS.items():
        if key.replace("-", "") in n:
            return bw
    return C.DEFAULT_VRAM_BW


def build_hardware(cfg=None, gpus=None, ram_gb=None):
    """Assemble a vramwise Hardware from detection + config overrides.
    gpus/ram_gb are injectable for tests; None triggers real detection."""
    cfg = cfg if cfg is not None else config.load()
    gpus = hardware.detect_gpus() if gpus is None else gpus
    vram_mib = sum((g.get("vram_mib") or 0) for g in gpus)
    ram_gb = hardware.detect_ram_gb() if ram_gb is None else ram_gb
    ram_gb = ram_gb or 16.0
    name = gpus[0]["name"] if gpus else "cpu"
    ov = (cfg or {}).get("vram_bandwidths") or {}
    return physics.Hardware(
        name=name,
        vram_gb=vram_mib / 1024.0,
        ram_gb=float(ram_gb),
        vram_bw=float(ov.get("vram_bw") or _preset_vram_bw(name)),
        ram_bw=float(ov.get("ram_bw") or C.DEFAULT_RAM_BW),
        disk_bw=float(ov.get("disk_bw") or C.DEFAULT_DISK_BW),
    )


_DEFAULT_BPW = 4.8   # unknown quant ~ q4


def _bpw_from_quant(quant):
    """(bpw, known?) from a quant label; falls back to a q4-ish default."""
    try:
        return catalog.resolve_quant(quant), True
    except (KeyError, AttributeError):
        return _DEFAULT_BPW, False


def _model_from_gguf(meta, size_bytes):
    """Build a vramwise Model from GGUF header facts + the file's real size.
    Returns (Model|None, confidence)."""
    if not size_bytes or size_bytes <= 0:
        return None, "unknown"
    bpw, known = _bpw_from_quant(meta.get("quantization") or "")
    total = size_bytes * 8.0 / bpw
    layers = int(meta.get("block_count") or 32)
    ec = meta.get("expert_count")
    eu = meta.get("expert_used_count")
    if ec and eu and ec > 1:
        active = min(total, total * (eu / ec) * 0.85 + total * 0.10)
        conf = "high" if known else "estimate"
    elif ec and ec > 1:
        active = total
        conf = "low"
    else:
        active = total
        conf = "high" if known else "estimate"
    return physics.Model(name=meta.get("name") or "model", total_params=total,
                         active_params=active, bpw=bpw, n_layers=layers), conf


def _mtime(path):
    try:
        return os.path.getmtime(path) if path and os.path.exists(path) else 0
    except OSError:
        return 0


def _hw_sig(hw):
    return (round(hw.vram_gb, 1), round(hw.ram_gb, 1), hw.vram_bw, hw.ram_bw, hw.disk_bw)


def _cache_get(key):
    with _CACHE_LOCK:
        return _CACHE.get(key)


def _cache_put(key, value):
    with _CACHE_LOCK:
        _CACHE[key] = value


def _normalize(pred, confidence, source):
    return {
        "regime": pred.regime,
        "tok_s": round(pred.tok_s, 1),
        "usability": physics.usability(pred.tok_s),
        "gpu_resident_frac": round(pred.gpu_resident_frac, 3),
        "time_budget_ms": {"disk": round(pred.t_disk_ms, 1),
                           "weight_read": round(pred.t_mem_ms, 1),
                           "compute": round(pred.t_compute_ms, 1)},
        "note": pred.note,
        "confidence": confidence,
        "source": source,
    }


def _unknown(note):
    return {"regime": None, "tok_s": None, "usability": None,
            "gpu_resident_frac": 0.0,
            "time_budget_ms": {"disk": 0, "weight_read": 0, "compute": 0},
            "note": note, "confidence": "unknown", "source": None}


def predict_local(gguf_path, size_bytes=None, cfg=None, context=4096, hw=None, meta=None):
    """Estimate for a model already on disk. Never raises.
    `meta` may be injected; otherwise it is read from gguf_path."""
    try:
        if size_bytes is None and gguf_path and os.path.exists(gguf_path):
            size_bytes = os.path.getsize(gguf_path)
        hw = hw if hw is not None else build_hardware(cfg)
        if meta is None:
            meta = (gguf.metadata(gguf_path) or {}) if gguf_path else {}
        key = ("local", gguf_path, _mtime(gguf_path), size_bytes, _hw_sig(hw), context)
        hit = _cache_get(key)
        if hit is not None:
            return hit
        model, conf = _model_from_gguf(meta, size_bytes)
        if model is None:
            return _unknown("couldn't read model size")
        out = _normalize(physics.predict(model, hw, context=context), conf, "gguf")
        _cache_put(key, out)
        return out
    except Exception:
        return _unknown("prediction unavailable")
