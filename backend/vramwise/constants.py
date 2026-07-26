"""Calibration constants for the vramwise speed model.

Every coefficient here is anchored to measurements from the sibling `new-inference-engine`
research project (a llama.cpp-oracle study of MoE inference on consumer hardware). The two
hard anchors the model is tuned to reproduce (see tests/test_anchors.py):

    GLM-5.2   754B MoE, UD-IQ4_XS (3.88 bpw), streamed from NVMe  -> 0.9 tok/s
    GLM-4.5-Air 106B/A12B, UD-Q2_K_XL (~3.5 bpw), resident         -> 19.5 tok/s

Both measured on: RTX 5080 16GB + RTX 5060 Ti 16GB (32GB VRAM), 31GB RAM,
WD_BLACK SN7100 NVMe (~5.7 GB/s deep-queue reads). That box is the DEFAULT_* baseline below.
"""

# --- usable-memory fractions (framework overhead, fragmentation, activations) ---
VRAM_USABLE_FRAC = 0.85   # of nominal VRAM, before KV cache
RAM_USABLE_FRAC = 0.70    # OS + app headroom on a typical desktop

# --- bandwidths (GB/s), overridable per hardware preset ---
DEFAULT_DISK_BW = 5.7     # SN7100 sustained deep-queue direct read (measured)
DEFAULT_RAM_BW = 50.0     # dual-channel DDR5 desktop, realistic sustained
DEFAULT_VRAM_BW = 500.0   # mid-range modern GPU effective; presets override per card

# --- compute / execution model ---
# Per-token execution reads the active (routed) weights from wherever they live and runs the
# matmul. Modeled as bandwidth-bound (VRAM vs RAM blend, set in physics) plus a fixed
# per-token floor for per-layer CPU<->GPU sync + sampling. Both coefficients are solved from
# the two measured anchors (Air 19.5 resident, GLM-5.2 0.9 streamed); see tests/test_anchors.
SYNC_FLOOR_MS = 33.0        # per-token fixed cost (per-layer sync + sampling), from the Air anchor

# When streaming, routed experts are cold-read from NVMe then computed on the CPU. The CPU
# matmul is memory-bandwidth bound at this effective rate (the measured GLM t_fix, minus the
# sync floor, over the per-token active bytes).
CPU_STREAM_BW = 10.4        # GB/s effective CPU expert-matmul rate while streaming

# Sustained streaming throughput is below the drive's peak deep-queue read; this efficiency
# reproduces the measured GLM t_io = 0.71 s for 3.4 GB.
STREAM_EFF = 0.84

# KV-cache bytes per token per layer is ~2 * n_kv_heads * head_dim * bytes; we approximate
# with a per-1k-context VRAM cost derived from a typical 7-70B attention config. Coarse by
# design (KV is a second-order term for the fit/speed verdict).
KV_GB_PER_1K_CONTEXT = 0.5

# quant name -> bits per weight (effective, including typical mixed-precision dynamic quants)
QUANT_BPW = {
    "f16": 16.0, "fp16": 16.0, "bf16": 16.0,
    "q8_0": 8.5, "q8": 8.5,
    "q6_k": 6.6, "q6": 6.6,
    "q5_k_m": 5.7, "q5_k_s": 5.5, "q5": 5.6,
    "q4_k_m": 4.9, "q4_k_s": 4.6, "q4_0": 4.5, "q4": 4.8, "iq4_xs": 4.3,
    "q3_k_m": 3.9, "q3_k_l": 4.1, "q3_k_s": 3.5, "iq3_xxs": 3.3, "q3": 3.9,
    "ud_q2_k_xl": 3.5, "q2_k": 3.4, "iq2_xxs": 2.4, "q2": 3.0,
    "iq1_m": 1.9, "iq1_s": 1.6,
}

# usability bands for the verdict line (tok/s, decode)
USABLE_INTERACTIVE = 10.0   # snappy chat
USABLE_OK = 3.0             # workable
USABLE_SLOW = 0.8           # batch/patience only
