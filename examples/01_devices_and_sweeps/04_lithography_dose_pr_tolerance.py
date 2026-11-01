"""Cookbook 04: Cleanroom Lithography Dose (Positive vs. Negative PR) & OPC Pre-Bias Array.

Demonstrates how over-dose and under-dose in E-beam / DUV lithography perturb `W_ring`, `W_bus`,
and `gap` in opposite directions simultaneously, and exports a 5-cell pre-compensated `.GDS`
bracket array so at least one resonator hits critical coupling on-wafer.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import (
    MRRDesignConfig,
    export_fab_bias_array_gds,
    run_fabrication_error_analysis,
    simulate_mrr_topology,
)


def main() -> None:
    # 1. Start from a critically coupled 220 nm SOI racetrack resonator at 1550 nm
    base = MRRDesignConfig(
        topology="racetrack_ap",
        core_material="Si",
        film_height_um=0.22,
        ring_width_um=0.48,
        bus_width_um=0.45,
        ring_radius_um=20.0,
        straight_length_um=8.0,
        gap_thru_um=0.20,
        wavelength_nm=1550.0,
        alpha_loss_db_per_cm=2.0,
    )
    cc = simulate_mrr_topology(base)["critical_coupling"]
    cfg_cc = replace(base, **{cc["parameter"]: float(cc["recommended_value"])})

    # 2. Compare Positive PR (ZEP520A / KrF-ArF DUV) vs. Negative PR (HSQ / ma-N 2403)
    for resist in ("positive_pr", "negative_pr"):
        res = run_fabrication_error_analysis(cfg_cc, resist_tone=resist, max_dose_error_pct=15.0)
        s = res["summary"]
        oc = s["over_dose_corner"]
        uc = s["under_dose_corner"]
        print(f"\n=== {res['resist_name_en']} ===")
        print(f"  Nominal (0% dose):    ER = {s['nominal_er_dB']:.1f} dB ({s['nominal_regime']})")
        print(
            f"  Over-Dose (+15%):     dCD = {oc['delta_cd_nm']:+.1f} nm, gap = {oc['gap_fab_um']*1000:.0f} nm "
            f"-> ER = {oc['extinction_ratio_dB']:.1f} dB ({oc['coupling_regime']}), dwl = {oc['delta_wl_res_nm']:+.2f} nm"
        )
        print(
            f"  Under-Dose (-15%):    dCD = {uc['delta_cd_nm']:+.1f} nm, gap = {uc['gap_fab_um']*1000:.0f} nm "
            f"-> ER = {uc['extinction_ratio_dB']:.1f} dB ({uc['coupling_regime']}), dwl = {uc['delta_wl_res_nm']:+.2f} nm"
        )
        print(
            f"  ER >= 15 dB Window:   CD span = {s['cd_window_er15_span_nm']:.1f} nm | "
            f"Dose span = {s['dose_window_er15_span_pct']:.1f}% | dl/dCD = {s['sensitivity_dl_dcd_pm_per_nm']:+.1f} pm/nm"
        )

    # 3. Export 5-cell pre-biased mask array (-20, -10, 0, +10, +20 nm)
    out_dir = REPO_ROOT / "outputs" / "cookbook_04_fab_tolerance"
    gds_info = export_fab_bias_array_gds(cfg_cc, out_dir / "SOI_OPC_DoseBracket_5x.gds")
    print(f"\nSaved 5-cell pre-biased foundry array: {gds_info['gds_path']}")


if __name__ == "__main__":
    main()
