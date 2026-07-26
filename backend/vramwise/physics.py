"""The speed model: from (model, hardware) -> placement regime + predicted tok/s.

Pure functions and dataclasses only; no I/O. This is the auditable core — every number in
the CLI output comes from here, and the two measured anchors are asserted in the tests.
"""
from __future__ import annotations
from dataclasses import dataclass
from . import constants as C


@dataclass
class Model:
    name: str
    total_params: float      # e.g. 754e9
    active_params: float     # per-token active params; == total for dense models
    bpw: float               # effective bits per weight of the chosen quant
    n_layers: int = 48

    @property
    def is_moe(self) -> bool:
        return self.active_params < self.total_params * 0.95

    @property
    def model_bytes(self) -> float:
        return self.total_params * self.bpw / 8.0

    @property
    def active_bytes_per_token(self) -> float:
        return self.active_params * self.bpw / 8.0


@dataclass
class Hardware:
    name: str
    vram_gb: float
    ram_gb: float
    disk_bw: float = C.DEFAULT_DISK_BW     # GB/s
    ram_bw: float = C.DEFAULT_RAM_BW       # GB/s
    vram_bw: float = C.DEFAULT_VRAM_BW     # GB/s


@dataclass
class Prediction:
    regime: str                # "gpu-resident" | "hybrid" | "streaming" | "won't-fit-quality"
    tok_s: float
    model_gb: float
    vram_avail_gb: float
    ram_avail_gb: float
    gpu_resident_frac: float   # fraction of model bytes living in VRAM
    t_disk_ms: float
    t_mem_ms: float
    t_compute_ms: float
    note: str

    @property
    def total_ms(self) -> float:
        return self.t_disk_ms + self.t_mem_ms + self.t_compute_ms


def _kv_gb(context: int) -> float:
    return C.KV_GB_PER_1K_CONTEXT * (context / 1000.0)


def predict(model: Model, hw: Hardware, context: int = 4096) -> Prediction:
    GB = 1e9
    model_gb = model.model_bytes / GB
    active_gb = model.active_bytes_per_token / GB

    vram_avail = max(hw.vram_gb * C.VRAM_USABLE_FRAC - _kv_gb(context), 0.0)
    ram_avail = hw.ram_gb * C.RAM_USABLE_FRAC

    # --- placement ---
    if model_gb <= vram_avail:
        regime = "gpu-resident"
        gpu_frac = 1.0
    elif model_gb <= vram_avail + ram_avail:
        regime = "hybrid"
        gpu_frac = vram_avail / model_gb if model_gb > 0 else 1.0
    else:
        regime = "streaming"
        gpu_frac = (vram_avail / model_gb) if model_gb > 0 else 0.0

    # --- per-token time components (seconds) ---
    # Fixed per-token floor: per-layer CPU<->GPU sync + sampling (from the Air anchor).
    sync = C.SYNC_FLOOR_MS / 1000.0
    cpu_share = 1.0 - gpu_frac

    if regime == "streaming":
        # Disk-bound: the per-token touched bytes that don't fit fast memory are cold-read from
        # NVMe, then computed on the CPU. Only the NON-resident fraction streams — for a dense
        # model most weights stay resident and are reused each token; for a big MoE the routed
        # hot set overflows the cache so nearly all of it misses.
        resident_frac = min(1.0, (vram_avail + ram_avail) / model_gb) if model_gb > 0 else 1.0
        streamed_gb = active_gb * (1.0 - resident_frac)
        t_disk = streamed_gb / (hw.disk_bw * C.STREAM_EFF)
        t_mem = active_gb / C.CPU_STREAM_BW      # CPU expert matmul over the touched bytes
        t_compute = sync
    else:
        # Resident: read active weights from where they live (VRAM/RAM blend by residency).
        t_disk = 0.0
        eff_bw = gpu_frac * hw.vram_bw + cpu_share * hw.ram_bw
        t_mem = active_gb / eff_bw if eff_bw > 0 else 0.0
        t_compute = sync

    t_token = t_disk + t_mem + t_compute
    tok_s = 1.0 / t_token if t_token > 0 else 0.0

    note = _recommend(regime, tok_s, model, hw, model_gb, vram_avail, ram_avail)
    return Prediction(
        regime=regime, tok_s=tok_s, model_gb=model_gb,
        vram_avail_gb=vram_avail, ram_avail_gb=ram_avail, gpu_resident_frac=gpu_frac,
        t_disk_ms=t_disk * 1000, t_mem_ms=t_mem * 1000, t_compute_ms=t_compute * 1000,
        note=note,
    )


def _recommend(regime, tok_s, model, hw, model_gb, vram_avail, ram_avail) -> str:
    if regime == "gpu-resident":
        return f"Fits entirely in VRAM — expect snappy, GPU-bound generation."
    if regime == "hybrid":
        over = model_gb - vram_avail
        return (f"Offloads ~{over:.0f} GB of experts/layers to CPU+RAM. Interactive if the "
                f"active set is small (MoE); dense models this size will be slower.")
    # streaming
    fast_mem = vram_avail + ram_avail
    short = model_gb / max(fast_mem, 1e-9)
    tip = "try a smaller quant" if model.bpw > 3.6 else "consider an Air-class / smaller sibling"
    return (f"Model is ~{short:.1f}x your fast memory — weights stream from disk every token. "
            f"Disk bandwidth is the wall; {tip}.")


def usability(tok_s: float) -> str:
    if tok_s >= C.USABLE_INTERACTIVE:
        return "interactive"
    if tok_s >= C.USABLE_OK:
        return "usable"
    if tok_s >= C.USABLE_SLOW:
        return "slow"
    return "impractical"
