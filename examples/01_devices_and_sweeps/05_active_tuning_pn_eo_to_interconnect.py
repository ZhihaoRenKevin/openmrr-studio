"""Cookbook 05: 2D-FEM Active Tuning (Si PN/PIN, Pockels EO, Thermo-Optic) & Lumerical INTERCONNECT.

Demonstrates 100% pure-Python, zero-COMSOL multiphysics active tuning in MicroRing Studio:
  1. Silicon Lateral PN Depletion (`0` to `-5 V`): 2D Debye depletion + Soref-Bennett complex
     `dn + i*dk` fed directly into the 2D conformal vector Maxwell eigenmode solver.
  2. Anisotropic Pockels EO (`X-cut TFLN`): 2D Laplace electrostatic FEM linking electrode gap `G`
     to core `E`-field & `V_pi*L`, plus direct `E-field [V/um]` spectra.
  3. Thermo-Optic `TiN` Microheater (`Si3N4`): 2D Fourier heat conduction FEM linking `BOX` oxide
     thickness & heater geometry to `R_th [K/mW]`, `P_pi [mW]`, and `f_3dB [kHz]`, plus direct `dT [K]`.
  4. Turnkey Ansys Lumerical INTERCONNECT export (`SPAR .dat`, `OMM n_eff .txt`, `.lsf`, `lumapi`, `.zip`).
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
    export_lumerical_interconnect_bundle,
    run_active_tuning_analysis,
    simulate_mrr_topology,
)


def main() -> None:
    out_root = REPO_ROOT / "outputs" / "cookbook_05_active_tuning"

    # -------------------------------------------------------------------------
    # 1. Silicon Lateral PN Depletion Modulator (220 nm SOI rib, 90 nm slab)
    # -------------------------------------------------------------------------
    soi_base = MRRDesignConfig(
        topology="point_circular_ap",
        core_material="Si",
        film_height_um=0.22,
        slab_height_um=0.09,
        ring_width_um=0.48,
        bus_width_um=0.44,
        ring_radius_um=20.0,
        gap_thru_um=0.20,
        wavelength_nm=1550.0,
        alpha_loss_db_per_cm=2.0,
        span_nm=6.0,
    )
    # Size bus-to-ring gap for ~11 dB/cm total doped PN cavity loss (~2 dB/cm roughness + ~9 dB/cm PN FCA)
    cc_soi = simulate_mrr_topology(replace(soi_base, alpha_loss_db_per_cm=11.0))["critical_coupling"]
    soi_cc = replace(soi_base, **{cc_soi["parameter"]: float(cc_soi["recommended_value"])})

    pn_res = run_active_tuning_analysis(
        soi_cc,
        mechanism="si_pn_depletion",
        drive_type="voltage_v",
        bias_values=[0.0, -1.0, -2.5, -5.0],
        na_p_cm3=5.0e17,
        nd_n_cm3=5.0e17,
        pn_offset_nm=25.0,
    )
    eff_pn = pn_res["efficiency"]
    gp_pn = pn_res["geometry_physics"]
    print("\n=== 1. Silicon Lateral PN Depletion (2D Debye + Soref-Bennett + Vector FEM) ===")
    print(
        f"  Slope = {eff_pn['wavelength_slope']} {eff_pn['wavelength_slope_unit']} | "
        f"V_pi*L = {eff_pn['V_pi_L_v_cm']} V*cm | f_3dB = {gp_pn['f_3db_eo_ghz']} GHz "
        f"(W_dep(0V) = {gp_pn['w_dep_0v_nm']} nm, R_s = {gp_pn['r_series_ohm']} Ohm)"
    )
    for st in pn_res["states"]:
        print(
            f"    {st['label']:>8s}: Re(n_eff)={st['neff_active_real']:.6f}, "
            f"alpha_tot={st['alpha_total_roundtrip_db_per_cm']:.2f} dB/cm, "
            f"d_lambda={st['resonance_shift_pm']:+.2f} pm, ER={st['ER_thru_dB']:.1f} dB"
        )

    ic_bundle = export_lumerical_interconnect_bundle(
        soi_cc, pn_res, out_root / "interconnect_soi_pn", make_zip=True
    )
    print(
        f"  Exported Lumerical INTERCONNECT bundle: {ic_bundle['zip_path']} "
        f"(passivity={ic_bundle['passivity_verified']}, {ic_bundle['num_freq_points']} freq pts)"
    )

    # -------------------------------------------------------------------------
    # 2. X-Cut TFLN Racetrack Pockels EO (2D Laplace Electrode Gap vs Direct E)
    # -------------------------------------------------------------------------
    tfln_cfg = MRRDesignConfig(
        topology="racetrack_ap",
        core_material="LN_Xcut",
        film_height_um=0.60,
        slab_height_um=0.30,
        ring_width_um=1.20,
        bus_width_um=1.00,
        ring_radius_um=60.0,
        straight_length_um=80.0,
        gap_thru_um=0.32,
        wavelength_nm=1550.0,
        span_nm=4.0,
    )
    print("\n=== 2. X-Cut TFLN Anisotropic Pockels EO (2D Laplace FEM & Direct E-Field) ===")
    for g_um in (5.0, 3.2):
        eo_v = run_active_tuning_analysis(
            tfln_cfg,
            mechanism="pockels_eo",
            drive_type="voltage_v",
            bias_values=[-10.0, 0.0, 10.0],
            electrode_gap_um=g_um,
        )
        print(
            f"  Electrode Gap G = {g_um:.1f} um -> E_x = {eo_v['geometry_physics']['ex_core_v_per_um_per_v']:.4f} (V/um)/V, "
            f"Slope = {eo_v['efficiency']['wavelength_slope']} pm/V, "
            f"V_pi*L = {eo_v['efficiency']['V_pi_L_v_cm']} V*cm, BW = {eo_v['efficiency']['bandwidth_3db']} GHz"
        )
    eo_e = run_active_tuning_analysis(
        tfln_cfg,
        mechanism="pockels_eo",
        drive_type="e_field_v_per_um",
        bias_values=[-8.0, 0.0, 8.0],
    )
    print(
        f"  Direct Core E-Field [-8, 0, +8 V/um] -> Slope = {eo_e['efficiency']['wavelength_slope']} "
        f"{eo_e['efficiency']['wavelength_slope_unit']}, E_pi = {eo_e['efficiency']['E_pi_v_per_um']} V/um"
    )

    # -------------------------------------------------------------------------
    # 3. Si3N4 Thermo-Optic TiN Microheater (2D Fourier FEM BOX Sweep & Direct dT)
    # -------------------------------------------------------------------------
    sin_cfg = MRRDesignConfig(
        topology="point_circular_ap",
        core_material="Si3N4",
        film_height_um=0.40,
        ring_width_um=1.20,
        bus_width_um=1.00,
        ring_radius_um=40.0,
        gap_thru_um=0.25,
        wavelength_nm=1550.0,
        span_nm=6.0,
    )
    print("\n=== 3. Si3N4 Thermo-Optic TiN Microheater (2D Fourier Heat FEM & Direct dT) ===")
    for box_um in (2.0, 3.5):
        to_i = run_active_tuning_analysis(
            sin_cfg,
            mechanism="thermo_optic",
            drive_type="current_ma",
            bias_values=[0.0, 4.0, 8.0],
            box_thickness_um=box_um,
        )
        print(
            f"  BOX = {box_um:.1f} um -> R_th = {to_i['geometry_physics']['r_th_core_k_per_mw']} K/mW, "
            f"P_pi = {to_i['efficiency']['P_pi_mw']} mW, "
            f"f_3dB = {to_i['efficiency']['bandwidth_3db']} kHz"
        )
    to_t = run_active_tuning_analysis(
        sin_cfg,
        mechanism="thermo_optic",
        drive_type="delta_temp_k",
        bias_values=[0.0, 25.0, 50.0],
    )
    print(
        f"  Direct Temperature [0, 25, 50 K] -> Slope = {to_t['efficiency']['wavelength_slope']} pm/K, "
        f"dT_pi = {to_t['efficiency']['delta_T_pi_k']} K"
    )


if __name__ == "__main__":
    main()
