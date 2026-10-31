"""Generate Publication-Grade Hero Overview Figure (`1x4` Panels) for OpenMRR Studio.

Follows Nature Photonics figure standards:
  - Font: Arial (panel tags `a–d` bold 9 pt, axis labels 8 pt, tick labels 7.5 pt)
  - Axes: 4-sided closed frame, inward ticks (`direction='in'`), zero background gridlines
  - Colormap: `inferno` for optical field magnitude |E|; colorblind-safe Okabe-Ito curves
  - Outputs: `docs/images/hero_openmrr_overview.png` (600 DPI) + `.svg` + per-panel CSVs
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from openmrr import (
    MRRDesignConfig,
    WaveguideCrossSectionSpec,
    fit_single_resonance_cmt,
    get_material_fn,
    run_mrr_parameter_sweep,
    simulate_mrr_topology,
    solve_modes_fem,
)
from openmrr.mrr_cmt_fit_predict import cmt_split_doublet_power


def apply_nature_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8.0,
        "axes.labelsize": 8.0,
        "axes.titlesize": 8.0,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 6.8,
        "axes.linewidth": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "axes.grid": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })


def main() -> None:
    apply_nature_style()
    img_dir = REPO_ROOT / "docs" / "images"
    csv_dir = REPO_ROOT / "outputs" / "hero_figure_csv"
    img_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 4, figsize=(11.2, 2.65), constrained_layout=True)

    # ------------------------------------------------------------------
    # Panel a: 2D Conformal Bent Waveguide Eigenmode (4H-SiC, R = 40 um)
    # ------------------------------------------------------------------
    ax = axes[0]
    spec = WaveguideCrossSectionSpec(
        w_bottom_um=1.10,
        h_film_um=0.60,
        h_slab_um=0.0,
        sidewall_deg=82.0,
        core_material_fn=get_material_fn("4H-SiC"),
        clad_material_fn=get_material_fn("SiO2"),
        top_clad_material_fn=get_material_fn("SiO2"),
        domain_width_um=3.6,
        h_box_um=1.2,
        h_top_clad_um=1.2,
    )
    modes = solve_modes_fem(
        spec,
        1550e-9,
        bend_radius_m=40e-6,
        num_modes=2,
        core_mesh_res_um=0.035,
        eval_grid_step_um=0.025,
        mesh_backend="bsd_conformal",
    )
    m0 = modes[0]
    e_mag = np.sqrt(np.abs(m0.Ex) ** 2 + np.abs(m0.Ey) ** 2 + np.abs(m0.Ez) ** 2)
    e_norm = e_mag / max(float(np.max(e_mag)), 1e-12)
    x_um = m0.x_m * 1e6
    y_um = m0.y_m * 1e6

    im = ax.pcolormesh(x_um, y_um, e_norm, cmap="inferno", shading="auto", vmin=0.0, vmax=1.0)
    core_poly = spec.build_polygons_um()["core"]
    cx, cy = core_poly.exterior.xy
    ax.plot(cx, cy, color="#DCE6F1", lw=1.1)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.45, 0.95)
    ax.set_xlabel("Radial coordinate x (um)")
    ax.set_ylabel("Vertical coordinate y (um)")
    ax.text(
        0.04, 0.91,
        f"4H-SiC R = 40 um\nn_eff = { float(np.real(m0.n_eff)):.4f}",
        transform=ax.transAxes, color="white", fontsize=7.0, va="top",
        bbox=dict(boxstyle="round,pad=0.2", fc="#0b101b", ec="none", alpha=0.65),
    )
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("Normalized |E| (arb. u.)", fontsize=7.2)
    cb.ax.tick_params(labelsize=6.8, direction="in")

    # Export Panel a slice CSV
    mid_j = int(np.argmin(np.abs(y_um - 0.30)))
    np.savetxt(
        csv_dir / "panel_a_bent_fem_mode_midslice.csv",
        np.column_stack([x_um, e_norm[mid_j, :]]),
        delimiter=",",
        header="x_um,normalized_E_midheight_arb",
        comments="",
    )

    # ------------------------------------------------------------------
    # Panel b: Pulley Wrap-Angle Sweep & Critical Coupling Synthesis
    # ------------------------------------------------------------------
    ax = axes[1]
    pulley_cfg = MRRDesignConfig(
        topology="pulley_ap",
        core_material="4H-SiC",
        film_height_um=0.60,
        sidewall_deg=82.0,
        ring_width_um=1.10,
        bus_width_um=0.82,
        ring_radius_um=40.0,
        gap_thru_um=0.26,
        pulley_angle_thru_deg=10.0,
        wavelength_nm=1550.0,
    )
    base_p = simulate_mrr_topology(pulley_cfg)
    theta_cc = float(base_p["critical_coupling"]["recommended_value"])
    angles = sorted(set(np.round(np.linspace(max(2.0, theta_cc * 0.3), theta_cc * 2.1, 13), 2).tolist() + [round(theta_cc, 3)]))
    sw = run_mrr_parameter_sweep(pulley_cfg, "pulley_angle_thru_deg", angles)

    er_clipped = np.minimum(sw["ER_thru_dB"], 58.0)
    ax.plot(sw["values"], er_clipped, "-o", color="#0072B2", ms=3.2, lw=1.2, label="Through ER [Simulated]")
    ax.axvline(theta_cc, color="#D55E00", ls="--", lw=1.0, label=f"theta_CC = {theta_cc:.1f} deg")
    ax.set_ylim(0.0, 68.0)
    ax.set_xlabel("Pulley wrap angle theta (deg)")
    ax.set_ylabel("Through extinction ratio (dB)")
    ax.legend(frameon=False, loc="upper right")

    np.savetxt(
        csv_dir / "panel_b_pulley_coupler_sweep.csv",
        np.column_stack([sw["values"], sw["ER_thru_dB"], sw["Q_loaded"]]),
        delimiter=",",
        header="pulley_angle_deg,through_extinction_ratio_dB,Q_loaded",
        comments="",
    )

    # ------------------------------------------------------------------
    # Panel c: X-cut TFLN Electro-Optic Racetrack Shift (0 V vs +25 V)
    # ------------------------------------------------------------------
    ax = axes[2]
    ln_0v = MRRDesignConfig(
        topology="racetrack_ad",
        core_material="LN_Xcut",
        film_height_um=0.60,
        slab_height_um=0.30,
        sidewall_deg=70.0,
        ring_width_um=1.40,
        bus_width_um=1.20,
        ring_radius_um=70.0,
        straight_length_um=60.0,
        gap_thru_um=0.28,
        gap_drop_um=0.30,
        wavelength_nm=1550.0,
        span_nm=2.6,
        num_spectrum_points=1400,
        voltage_v=0.0,
    )
    r0_scout = simulate_mrr_topology(ln_0v)
    wl_scout = np.asarray(r0_scout["spectrum"]["wavelength_nm"])
    lam_res0 = float(wl_scout[int(np.argmin(r0_scout["spectrum"]["thru_dB"]))])
    ln_zoom = replace(ln_0v, wavelength_nm=lam_res0, span_nm=0.22, num_spectrum_points=900)
    r0 = simulate_mrr_topology(ln_zoom)
    r25 = simulate_mrr_topology(replace(ln_zoom, voltage_v=25.0))
    wl_0 = (np.asarray(r0["spectrum"]["wavelength_nm"]) - lam_res0) * 1e3
    wl_25 = (np.asarray(r25["spectrum"]["wavelength_nm"]) - lam_res0) * 1e3

    ax.plot(wl_0, r0["spectrum"]["thru_dB"], color="#2B5B84", lw=1.15, label="Through (0 V)")
    ax.plot(wl_25, r25["spectrum"]["thru_dB"], color="#D55E00", lw=1.15, ls="--", label="Through (+25 V)")
    ax.plot(wl_0, r0["spectrum"]["drop_dB"], color="#009E73", lw=1.0, alpha=0.88, label="Drop (0 V)")
    ax.set_xlim(-105.0, 105.0)
    ax.set_ylim(-26.0, 1.8)
    ax.set_xlabel(f"Detuning from {lam_res0:.2f} nm (pm)")
    ax.set_ylabel("Transmission (dB)")
    ax.legend(frameon=False, loc="lower right")

    r25_interp = np.interp(
        r0["spectrum"]["wavelength_nm"],
        r25["spectrum"]["wavelength_nm"],
        r25["spectrum"]["thru_dB"],
    )
    np.savetxt(
        csv_dir / "panel_c_tfln_eo_tuning.csv",
        np.column_stack([
            r0["spectrum"]["wavelength_nm"],
            r0["spectrum"]["thru_dB"],
            r0["spectrum"]["drop_dB"],
            r25_interp,
        ]),
        delimiter=",",
        header="wavelength_nm,thru_0V_dB,drop_0V_dB,thru_25V_dB",
        comments="",
    )

    # ------------------------------------------------------------------
    # Panel d: CW/CCW Backscattering Split-Doublet CMT Parameter Fit
    # ------------------------------------------------------------------
    ax = axes[3]
    rng = np.random.default_rng(2026)
    wl_d = np.linspace(1550.47, 1550.53, 220)
    y_noisy = cmt_split_doublet_power(
        wl_d,
        lambda0_nm=1550.500,
        kappa_int_ghz=0.17,
        kappa_ext_ghz=0.14,
        mu_split_ghz=0.27,
        baseline_level=0.98,
        baseline_slope_per_nm=-0.02,
    ) + rng.normal(0.0, 0.006, len(wl_d))
    summary, y_fit, _ = fit_single_resonance_cmt(wl_d, y_noisy, model_type="auto", known_regime="undercoupled")
    det_pm = (wl_d - summary.lambda0_nm) * 1e3

    ax.plot(
        det_pm[::2], y_noisy[::2], "o",
        mfc="none", mec="#475569", mew=0.7, ms=3.0, label="Synthetic noisy trace"
    )
    ax.plot(det_pm, y_fit, color="#CC79A7", lw=1.4, label=f"CMT fit (Q_int={summary.Q_int/1e6:.2f}M)")
    ax.set_xlabel("Detuning Delta_lambda (pm)")
    ax.set_ylabel("Normalized transmission (arb. u.)")
    ax.set_ylim(0.18, 1.06)
    ax.legend(frameon=False, loc="lower right")

    np.savetxt(
        csv_dir / "panel_d_cmt_doublet_fit.csv",
        np.column_stack([wl_d, y_noisy, y_fit]),
        delimiter=",",
        header="wavelength_nm,synthetic_noisy_transmission,cmt_fit_transmission",
        comments="",
    )

    # Panel labels a, b, c, d (lowercase bold 9 pt Arial)
    for idx, panel_tag in enumerate(("a", "b", "c", "d")):
        axes[idx].text(
            -0.14, 1.05, panel_tag,
            transform=axes[idx].transAxes,
            fontsize=9.0, fontweight="bold", va="bottom", ha="left",
        )

    out_png = img_dir / "hero_openmrr_overview.png"
    out_svg = img_dir / "hero_openmrr_overview.svg"
    fig.savefig(out_png, dpi=600)
    fig.savefig(out_svg)
    plt.close(fig)
    print(f"Saved 600 DPI PNG : {out_png}")
    print(f"Saved Vector SVG  : {out_svg}")


if __name__ == "__main__":
    main()
