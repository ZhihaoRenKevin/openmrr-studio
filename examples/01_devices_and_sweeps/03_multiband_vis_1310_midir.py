"""Cookbook 03: Multi-Waveband MRR Design from Visible (532 nm) to Mid-IR (7.5 um).

Demonstrates designing and synthesizing critically coupled microring resonators across
five major integrated-photonics wavebands without commercial licenses:
  1. Visible Green (532 nm)       : 180 nm Si3N4 strip on SiO2 (bio-sensing / AR-VR)
  2. Quantum / VNIR (780 nm)      : 220 nm ALD TiO2 strip on SiO2 (Rb / atomic photonics)
  3. Datacom O-Band (1310 nm)     : 220 nm SOI 4-port add-drop WDM filter
  4. Telecom C-Band (1550 nm)     : 600 nm X-cut TFLN electro-optic racetrack
  5. Mid-IR Gas Sensing (4200 nm) : 1400 nm Ge rib on CaF2 (CO2 absorption band)
  6. LWIR Fingerprint (7500 nm)   : 2200 nm Ge strip on Si substrate
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import MRRDesignConfig, simulate_mrr_topology


MULTIBAND_DESIGNS = [
    (
        "Visible 532 nm (Si3N4)",
        MRRDesignConfig(
            topology="point_circular_ap",
            core_material="Si3N4",
            clad_material="SiO2",
            top_clad_material="SiO2",
            film_height_um=0.18,
            ring_width_um=0.38,
            bus_width_um=0.34,
            ring_radius_um=25.0,
            gap_thru_um=0.14,
            wavelength_nm=532.0,
            span_nm=2.2,
            polarization="TE0",
        ),
    ),
    (
        "VNIR 780 nm (TiO2)",
        MRRDesignConfig(
            topology="point_circular_ap",
            core_material="TiO2",
            clad_material="SiO2",
            top_clad_material="SiO2",
            film_height_um=0.20,
            ring_width_um=0.42,
            bus_width_um=0.36,
            ring_radius_um=30.0,
            gap_thru_um=0.16,
            wavelength_nm=780.0,
            span_nm=3.5,
            polarization="TE0",
        ),
    ),
    (
        "O-Band 1310 nm (220nm SOI)",
        MRRDesignConfig(
            topology="point_circular_ad",
            core_material="Si",
            clad_material="SiO2",
            top_clad_material="SiO2",
            film_height_um=0.22,
            ring_width_um=0.40,
            bus_width_um=0.38,
            ring_radius_um=15.0,
            gap_thru_um=0.16,
            gap_drop_um=0.20,
            wavelength_nm=1310.0,
            span_nm=10.0,
            polarization="TE0",
        ),
    ),
    (
        "Mid-IR 4200 nm (Ge on CaF2)",
        MRRDesignConfig(
            topology="racetrack_ap",
            core_material="Ge",
            clad_material="CaF2",
            top_clad_material="Air",
            film_height_um=1.40,
            slab_height_um=0.30,
            sidewall_deg=84.0,
            ring_width_um=2.00,
            bus_width_um=2.00,
            ring_radius_um=65.0,
            straight_length_um=18.0,
            gap_thru_um=0.35,
            wavelength_nm=4200.0,
            span_nm=35.0,
            polarization="TE0",
        ),
    ),
    (
        "LWIR 7500 nm (Ge on Si)",
        MRRDesignConfig(
            topology="racetrack_ap",
            core_material="Ge",
            clad_material="Si",
            top_clad_material="Air",
            film_height_um=2.20,
            slab_height_um=0.0,
            sidewall_deg=86.0,
            ring_width_um=2.60,
            bus_width_um=2.60,
            ring_radius_um=95.0,
            straight_length_um=25.0,
            gap_thru_um=0.30,
            wavelength_nm=7500.0,
            span_nm=65.0,
            polarization="TE0",
        ),
    ),
]


def main() -> None:
    print("=" * 98)
    print(f"{'Waveband Platform':<28} | {'lam [nm]':>8} | {'n_eff':>7} | {'n_g':>7} | {'FSR [nm]':>8} | {'Q_L (CC)':>10} | {'ER [dB]':>7}")
    print("-" * 98)
    for label, cfg in MULTIBAND_DESIGNS:
        scout = simulate_mrr_topology(cfg)
        cc = scout["critical_coupling"]
        cfg_cc = replace(cfg, **{cc["parameter"]: float(cc["recommended_value"])})
        res = simulate_mrr_topology(cfg_cc)
        m = res["metrics"]
        print(
            f"{label:<28} | {cfg.wavelength_nm:8.1f} | {m['neff_ring']:7.4f} | {m['ng_ring']:7.4f} | "
            f"{m['FSR_nm']:8.3f} | {m['Q_loaded']:10,.0f} | {m['ER_thru_dB']:7.1f}"
        )
    print("=" * 98)


if __name__ == "__main__":
    main()
