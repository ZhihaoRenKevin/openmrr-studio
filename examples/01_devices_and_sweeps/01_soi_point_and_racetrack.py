"""Recipe 01a: 220 nm SOI Point-Coupled & 4-Port Racetrack Microring Synthesis + Gap Sweep.

Run:
    uv run python examples/01_devices_and_sweeps/01_soi_point_and_racetrack.py
"""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from openmrr import MRRDesignConfig, run_mrr_parameter_sweep, simulate_mrr_topology

# ---------------- Top-Level Physical & Geometric Parameters ----------------
WAVELENGTH_NM = 1550.0        # unit: nm
H_FILM_UM = 0.22              # unit: um (220 nm SOI)
W_RING_UM = 0.50              # unit: um
W_BUS_UM = 0.45               # unit: um
RADIUS_UM = 15.0              # unit: um
STRAIGHT_LS_UM = 8.0          # unit: um
GAP_SWEEP_UM = [0.14, 0.17, 0.20, 0.23, 0.26]  # unit: um
# ---------------------------------------------------------------------------


def main() -> None:
    cfg_rt = MRRDesignConfig(
        topology="racetrack_ad",
        core_material="Si",
        clad_material="SiO2",
        top_clad_material="SiO2",
        film_height_um=H_FILM_UM,
        slab_height_um=0.0,
        sidewall_deg=86.0,
        ring_width_um=W_RING_UM,
        bus_width_um=W_BUS_UM,
        ring_radius_um=RADIUS_UM,
        straight_length_um=STRAIGHT_LS_UM,
        gap_thru_um=0.20,
        gap_drop_um=0.20,
        wavelength_nm=WAVELENGTH_NM,
        span_nm=14.0,
    )
    res = simulate_mrr_topology(cfg_rt)
    m = res["metrics"]
    print("=== 220 nm SOI 4-Port Add-Drop Racetrack MRR ===")
    print(f"n_eff = {m['neff_ring']:.5f}, n_g = {m['ng_ring']:.5f}")
    print(f"FSR   = {m['FSR_GHz']:.2f} GHz ({m['FSR_nm']:.3f} nm)")
    print(f"Q_L   = {m['Q_loaded']:,.0f} | Through ER = {m['ER_thru_dB']:.2f} dB")

    # Sweep gap on 2-port all-pass circular SOI ring
    cfg_ap = MRRDesignConfig(
        topology="point_circular_ap",
        core_material="Si",
        film_height_um=H_FILM_UM,
        ring_width_um=W_RING_UM,
        bus_width_um=W_BUS_UM,
        ring_radius_um=RADIUS_UM,
        wavelength_nm=WAVELENGTH_NM,
    )
    sw = run_mrr_parameter_sweep(cfg_ap, "gap_thru_um", GAP_SWEEP_UM)
    print("\n--- Coupler Gap Sweep (2-Port SOI Circular All-Pass) ---")
    for g, ql, er in zip(sw["values"], sw["Q_loaded"], sw["ER_thru_dB"]):
        print(f"gap = {g*1000:5.0f} nm  ->  Q_loaded = {ql:8,.0f}  |  ER = {er:5.1f} dB")


if __name__ == "__main__":
    main()
