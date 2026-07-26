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
