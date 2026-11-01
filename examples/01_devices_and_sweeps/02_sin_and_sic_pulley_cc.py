"""Recipe 01b: 4H-SiC Pulley Critical Coupling & X-cut TFLN Pockels EO Racetrack.

Demonstrates:
  1. Concentric wrap-around pulley coupler phase-matching & exact critical-coupling
     angle synthesis (`theta_CC`) on 600 nm c-cut 4H-SiC.
  2. Electro-optic resonance tuning (`pm/V`) on 600 nm X-cut TFLN (`r_33 = 30.9 pm/V`
     along the Y-propagating racetrack straight arms, plus azimuthal bend averaging).

Run:
    uv run python examples/01_devices_and_sweeps/02_sin_and_sic_pulley_cc.py
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import MRRDesignConfig, simulate_mrr_topology


def main() -> None:
    # Part 1: 4H-SiC Pulley All-Pass Critical Coupling Synthesis
    sic_cfg = MRRDesignConfig(
        topology="pulley_ap",
        core_material="4H-SiC",
        clad_material="SiO2",
        top_clad_material="SiO2",
        film_height_um=0.60,
        slab_height_um=0.0,
        sidewall_deg=82.0,
        ring_width_um=1.10,
        bus_width_um=0.82,
        ring_radius_um=40.0,
        gap_thru_um=0.24,
        pulley_angle_thru_deg=15.0,
        wavelength_nm=1550.0,
    )
    init_res = simulate_mrr_topology(sic_cfg)
    theta_cc = float(init_res["critical_coupling"]["recommended_value"])
    cc_res = simulate_mrr_topology(replace(sic_cfg, pulley_angle_thru_deg=theta_cc))
    m = cc_res["metrics"]

    print("=== 1. 4H-SiC Concentric Pulley MRR (Critical Coupling Synthesis) ===")
    print(f"Synthesized theta_CC : {theta_cc:.3f} deg (at gap = {sic_cfg.gap_thru_um*1000:.0f} nm)")
    print(f"Loaded / Intrinsic Q : Q_L = {m['Q_loaded']:,.0f} | Q_int = {m['Q_int']:,.0f}")
    print(f"Extinction Ratio     : {m['ER_thru_dB']:.1f} dB (FSR = {m['FSR_GHz']:.2f} GHz)")

    # Part 2: X-cut Thin-Film Lithium Niobate (TFLN) EO Racetrack
    tfln_cfg = MRRDesignConfig(
        topology="racetrack_ap",
        core_material="LN_Xcut",
        clad_material="SiO2",
        top_clad_material="SiO2",
        film_height_um=0.60,
        slab_height_um=0.30,
        sidewall_deg=70.0,
        ring_width_um=1.40,
        bus_width_um=1.20,
        ring_radius_um=80.0,
        straight_length_um=60.0,
        gap_thru_um=0.30,
        voltage_v=15.0,
        electrode_gap_um=5.0,
        wavelength_nm=1550.0,
    )
    eo_res = simulate_mrr_topology(tfln_cfg)
    em = eo_res["metrics"]
    print("\n=== 2. X-cut TFLN Racetrack Electro-Optic Modulator (+15 V Bias) ===")
    print(f"FSR = {em['FSR_GHz']:.2f} GHz | Q_L = {em['Q_loaded']:,.0f}")
    print(f"Resonance EO Shift   : {em['tuning_shift_pm']:+.2f} pm ({em['eo_tunability_pm_per_v']:.2f} pm/V)")


if __name__ == "__main__":
    main()
