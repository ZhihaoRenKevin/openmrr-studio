"""Recipe 06: Butt/Edge Couplers, 2D-FDFD Grating Couplers & High-Q FDTD Convergence Analysis.

Demonstrates three major capabilities in MicroRing Studio v3.5.0 without Lumerical, COMSOL, or RSoft:
  1. Butt / Edge Coupler (Inverse-Taper Spot-Size Converter) to Lensed Fiber & III-V DFB Laser Diode
     solved via 2D conformal vector Maxwell FEM + complex Poynting overlap + adiabatic EME.
  2. Surface Grating Coupler (Uniform vs Gaussian-Apodized Focusing Curved-Groove) solved via
     Bragg synthesis + Native 2D Full-Wave Maxwell FDFD (UPML), plus 127-um FA Ring Loopback .GDS.
  3. Ultra-High-Q (Q > 2,000,000) Ring-Down Diagnostics quantifying why full-ring 3D FDTD fails to
     converge vs MicroRing Studio's exact infinite-roundtrip solver + Coupler-Only 3D-FDTD Cutout.

Run:
    python examples/01_devices_and_sweeps/06_butt_gc_couplers_and_high_q_fdtd.py
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
    analyze_high_q_fdtd_convergence,
    design_butt_edge_coupler,
    design_grating_coupler,
    export_coupler_cutout_gds,
    export_io_coupler_gds,
    export_io_coupler_interconnect,
    simulate_mrr_topology,
)


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "cookbook_06_io_and_highq"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("1. Butt / Edge Coupler (2D Vector Maxwell FEM + Poynting Overlap + Adiabatic EME)")
    print("=" * 80)
    butt_lensed = design_butt_edge_coupler(
        core_material="Si",
        wavelength_nm=1550.0,
        film_height_um=0.22,
        w_bus_um=0.48,
        fiber_preset="Lensed_2p5um",
        taper_length_um=160.0,
        taper_profile="adiabatic",
        ar_coating=True,
        box_thickness_um=3.0,
    )
    bm = butt_lensed["metrics"]
    print(
        f"[SOI -> Lensed 2.5 um] Optimal W_tip = {butt_lensed['w_tip_optimal_um']*1e3:.0f} nm | "
        f"Total IL = {bm['total_il_db']:.2f} dB ({bm['total_efficiency_pct']:.1f}%) | "
        f"1-dB Align Tol = (+/-{bm['tol_1db_x_um']:.2f}, +/-{bm['tol_1db_y_um']:.2f}) um | "
        f"Rec L_taper = {butt_lensed['recommended_taper_length_um']:.0f} um ({butt_lensed['elapsed_ms']:.0f} ms)"
    )

    butt_dfb = design_butt_edge_coupler(
        core_material="Si3N4",
        wavelength_nm=1310.0,
        film_height_um=0.40,
        w_bus_um=0.85,
        fiber_preset="DFB_Laser_Butt",
        taper_length_um=150.0,
        taper_profile="adiabatic",
        ar_coating=True,
        box_thickness_um=3.0,
    )
    dm = butt_dfb["metrics"]
    print(
        f"[Si3N4 O-Band -> III-V DFB Laser 2.4x1.2 um] Optimal W_tip = {butt_dfb['w_tip_optimal_um']*1e3:.0f} nm | "
        f"Total IL = {dm['total_il_db']:.2f} dB ({dm['total_efficiency_pct']:.1f}%) | "
        f"1-dB Align Tol = (+/-{dm['tol_1db_x_um']:.2f}, +/-{dm['tol_1db_y_um']:.2f}) um"
    )
    butt_gds = export_io_coupler_gds(butt_lensed, out_dir / "soi_butt_coupler.gds")
    butt_ic = export_io_coupler_interconnect(butt_lensed, out_dir / "ic_butt")
    print(f"  Exported Butt Coupler GDS: {butt_gds['gds_path']} | INTERCONNECT passivity={butt_ic['passivity_verified']}")

    print("\n" + "=" * 80)
    print("2. Surface Grating Coupler (Bragg Synthesis + Native 2D Full-Wave Maxwell FDFD)")
    print("=" * 80)
    gc_uni = design_grating_coupler(
        core_material="Si",
        wavelength_nm=1550.0,
        film_height_um=0.22,
        etch_depth_um=0.07,
        fiber_angle_deg=10.0,
        apodized=False,
        focusing=True,
        box_thickness_um=2.0,
        fiber_preset="SMF28_1550",
    )
    um = gc_uni["metrics"]
    print(
        f"[Uniform 220nm SOI GC] Pitch = {gc_uni['synthesis']['pitch_mean_um']*1e3:.1f} nm | "
        f"Peak IL = {um['peak_il_db']:.2f} dB ({um['peak_efficiency_pct']:.1f}%) @ {um['peak_wavelength_nm']:.1f} nm | "
        f"1-dB/3-dB BW = {um['bw_1db_nm']:.1f} / {um['bw_3db_nm']:.1f} nm | S11 = {um['back_reflection_s11_db']:.1f} dB"
    )

    gc_apo = design_grating_coupler(
        core_material="Si",
        wavelength_nm=1550.0,
        film_height_um=0.22,
        etch_depth_um=0.07,
        fiber_angle_deg=10.0,
        apodized=True,
        focusing=True,
        box_thickness_um=2.0,
        fiber_preset="SMF28_1550",
    )
    am = gc_apo["metrics"]
    print(
        f"[Apodized Focusing SOI GC] Mean Pitch = {gc_apo['synthesis']['pitch_mean_um']*1e3:.1f} nm "
        f"(ff {gc_apo['synthesis']['ff_start']:.2f}->{gc_apo['synthesis']['ff_end']:.2f}) | "
        f"Peak IL = {am['peak_il_db']:.2f} dB ({am['peak_efficiency_pct']:.1f}%) @ {am['peak_wavelength_nm']:.1f} nm | "
        f"1-dB/3-dB BW = {am['bw_1db_nm']:.1f} / {am['bw_3db_nm']:.1f} nm | S11 = {am['back_reflection_s11_db']:.1f} dB "
        f"({gc_apo['elapsed_ms']:.0f} ms)"
    )

    gc_loop_gds = export_io_coupler_gds(
        gc_apo,
        out_dir / "soi_focusing_gc_ring_loopback.gds",
        include_ring_loopback=True,
    )
    gc_ic = export_io_coupler_interconnect(gc_apo, out_dir / "ic_gc")
    print(f"  Exported Focusing GC + 127um FA Ring Loopback GDS: {gc_loop_gds['gds_path']} ({gc_loop_gds['cells']})")
    print(f"  Exported GC INTERCONNECT Bundle: {gc_ic['zip_path']} (passivity={gc_ic['passivity_verified']})")

    print("\n" + "=" * 80)
    print("3. Ultra-High-Q Ring-Down vs Lumerical FDTD Non-Convergence Analysis")
    print("=" * 80)
    cfg_hq = MRRDesignConfig(
        topology="pulley_ap",
        core_material="Si3N4",
        film_height_um=0.40,
        ring_width_um=1.30,
        bus_width_um=0.95,
        ring_radius_um=80.0,
        gap_thru_um=0.35,
        pulley_angle_thru_deg=14.0,
        wavelength_nm=1550.0,
        alpha_loss_db_per_cm=0.06,  # Ultra-low-loss LPCVD Si3N4 (~Q_int > 4 Million!)
    )
    scout = simulate_mrr_topology(cfg_hq)
    cc_param = scout["critical_coupling"]["parameter"]
    cc_val = float(scout["critical_coupling"]["recommended_value"])
    cfg_hq = replace(cfg_hq, **{cc_param: cc_val})

    hq = analyze_high_q_fdtd_convergence(cfg_hq, sim_times_ps=[10.0, 100.0, 1000.0])
    cut = export_coupler_cutout_gds(cfg_hq, out_dir)
    print(
        f"[Ultra-High-Q Si3N4] Q_loaded = {hq['Q_loaded']:,.0f} (FWHM = {hq['FWHM_pm']:.3f} pm, tau_ph = {hq['photon_lifetime_ps']:.1f} ps)\n"
        f"  Required 3D-FDTD time for 1e-5 shutoff = {hq['required_fdtd_sim_time_1e5_ns']:.2f} ns "
        f"({hq['required_fdtd_roundtrips_1e5']:,.0f} round-trips!)\n"
        f"  Converged Infinite-Roundtrip ER        = {hq['true_converged_er_db']:.2f} dB"
    )
    for tr in hq["truncated_fdtd_traces"]:
        print(
            f"  -> Truncated FDTD @ t_sim = {tr['fdtd_sim_time_ps']:6.1f} ps ({tr['completed_roundtrips']:4d} RTs, "
            f"shutoff={tr['residual_energy_shutoff']:.3f}): Apparent ER = {tr['apparent_er_db']:5.2f} dB "
            f"(error = {tr['er_error_db']:.2f} dB!)"
        )
    print(
        f"  Coupler-Only Non-Resonant FDTD Cutout  = {hq['coupler_only_fdtd_time_ps']:.2f} ps "
        f"({hq['time_domain_speedup_factor']:,.0f}x faster): {cut['gds_path']}"
    )


if __name__ == "__main__":
    main()
