"""Local Multi-Waveband Cross-Solver Benchmark & Lumerical Export Generator.

1. Runs 5 canonical multi-waveband photonic resonator benchmarks on macOS / Linux / Windows
   spanning Visible (532 nm), VNIR (780 nm), O-Band (1310 nm), C-Band (1550 nm), and Mid-IR (4200 nm).
2. Cross-checks two independent Maxwell eigenmode formulations locally:
     - Engine A: Pure-BSD 2nd-Order Conformal Vector FEM (`scikit-fem` `ElementTriN2 * ElementTriP2`)
     - Engine B: Structured Yee-Grid Finite-Difference Eigenmode (`tidy3d` local CPU FDE,
       same Yee-cell discretization family as Ansys Lumerical MODE FDE)
3. Exports:
     - `outputs/microring_vs_fde_multiband.csv` (unit-labeled columns)
     - `outputs/LOCAL_CROSSCHECK_REPORT.md`
     - Canonical `.gds` layout files + `outputs/lumerical_cases.json` for 1-command head-to-head
       execution against Ansys Lumerical `MODE FDE` + `3D FDTD` via `run_lumapi_validation.py`.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring.eigenmode_solver import (
    WaveguideCrossSectionSpec,
    solve_modes_fde_tidy3d,
    solve_modes_fem,
)
from microring.materials import T_REF_K, get_material_fn
from microring.mrr_topologies import MRRDesignConfig, export_mrr_gds, simulate_mrr_topology

OUT_DIR = Path(__file__).resolve().parent / "outputs"

# ==============================================================================
# Centralized Benchmark Parameter Table (all physical units explicitly declared)
# ==============================================================================
BENCHMARK_CASES: list[dict] = [
    {
        "case_id": "Vis_532nm_Si3N4_Strip",
        "topology": "point_circular_ap",
        "core_material": "Si3N4",
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 532.0,
        "film_height_um": 0.18,
        "slab_height_um": 0.0,
        "sidewall_deg": 88.0,
        "ring_width_um": 0.38,
        "bus_width_um": 0.34,
        "ring_radius_um": 25.0,
        "gap_thru_um": 0.14,
        "straight_length_um": 0.0,
        "pulley_angle_thru_deg": 20.0,
    },
    {
        "case_id": "VNIR_780nm_TiO2_Strip",
        "topology": "point_circular_ap",
        "core_material": "TiO2",
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 780.0,
        "film_height_um": 0.20,
        "slab_height_um": 0.0,
        "sidewall_deg": 86.0,
        "ring_width_um": 0.42,
        "bus_width_um": 0.36,
        "ring_radius_um": 30.0,
        "gap_thru_um": 0.16,
        "straight_length_um": 0.0,
        "pulley_angle_thru_deg": 20.0,
    },
    {
        "case_id": "OBand_1310nm_SOI_220nm",
        "topology": "point_circular_ad",
        "core_material": "Si",
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1310.0,
        "film_height_um": 0.22,
        "slab_height_um": 0.0,
        "sidewall_deg": 90.0,
        "ring_width_um": 0.40,
        "bus_width_um": 0.38,
        "ring_radius_um": 15.0,
        "gap_thru_um": 0.16,
        "straight_length_um": 0.0,
        "pulley_angle_thru_deg": 20.0,
    },
    {
        "case_id": "CBand_1550nm_4HSiC_Pulley",
        "topology": "pulley_ap",
        "core_material": "4H-SiC",
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "film_height_um": 0.60,
        "slab_height_um": 0.0,
        "sidewall_deg": 82.0,
        "ring_width_um": 1.05,
        "bus_width_um": 0.85,
        "ring_radius_um": 40.0,
        "gap_thru_um": 0.25,
        "straight_length_um": 0.0,
        "pulley_angle_thru_deg": 28.0,
    },
    {
        "case_id": "MidIR_4200nm_Ge_CaF2",
        "topology": "racetrack_ap",
        "core_material": "Ge",
        "clad_material": "CaF2",
        "top_clad_material": "Air",
        "wavelength_nm": 4200.0,
        "film_height_um": 1.40,
        "slab_height_um": 0.30,
        "sidewall_deg": 90.0,
        "ring_width_um": 2.00,
        "bus_width_um": 2.00,
        "ring_radius_um": 65.0,
        "gap_thru_um": 0.35,
        "straight_length_um": 18.0,
        "pulley_angle_thru_deg": 20.0,
    },
]


def _pick_te0(modes: list) -> object:
    te_modes = [m for m in modes if m.te_fraction >= 0.5]
    pool = te_modes if te_modes else modes
    return max(pool, key=lambda m: float(np.real(m.n_eff)))


def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gds_dir = OUT_DIR / "gds"
    gds_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    exported_cases = []

    for c in BENCHMARK_CASES:
        wl_nm = float(c["wavelength_nm"])
        wl_m = wl_nm * 1e-9
        wl_um = wl_nm * 1e-3
        wl_scale = float(np.clip(wl_nm / 1550.0, 0.35, 3.50))

        cfn = get_material_fn(c["core_material"])
        clfn = get_material_fn(c["clad_material"])
        tpfn = get_material_fn(c["top_clad_material"])
        mc = cfn(wl_m, T_REF_K)
        mcl = clfn(wl_m, T_REF_K)
        mtp = tpfn(wl_m, T_REF_K)

        box_pad = max(2.0, 1.35 * wl_um)
        dom_w = max(4.2 * wl_scale, c["ring_width_um"] + 2.6 * wl_um)
        fem_res = 0.020 if c["core_material"] == "Si" else round(float(np.clip(0.030 * wl_scale, 0.015, 0.085)), 4)
        fde_dl = (
            0.010 if c["core_material"] == "Si"
            else (0.025 if c["core_material"] == "Ge" else round(float(np.clip(0.018 * wl_scale, 0.012, 0.050)), 4))
        )

        spec = WaveguideCrossSectionSpec(
            w_bottom_um=c["ring_width_um"],
            h_film_um=c["film_height_um"],
            h_slab_um=c["slab_height_um"],
            sidewall_deg=c["sidewall_deg"],
            core_material_fn=cfn,
            clad_material_fn=clfn,
            top_clad_material_fn=tpfn,
            domain_width_um=dom_w,
            h_box_um=box_pad,
            h_top_clad_um=box_pad,
        )
        r_m = c["ring_radius_um"] * 1e-6

        m_fem = _pick_te0(
            solve_modes_fem(
                spec,
                wl_m,
                bend_radius_m=r_m,
                num_modes=4,
                core_mesh_res_um=fem_res,
                clad_mesh_res_um=max(fem_res * 5.0, 0.16 * wl_scale),
                export_grid=False,
                mesh_backend="bsd_conformal",
            )
        )
        m_fde = _pick_te0(
            solve_modes_fde_tidy3d(
                spec,
                wl_m,
                bend_radius_m=r_m,
                num_modes=4,
                core_dl_um=fde_dl,
            )
        )

        # Full MicroRing resonator + coupler synthesis + GDS export
        cfg = MRRDesignConfig(
            topology=c["topology"],
            core_material=c["core_material"],
            clad_material=c["clad_material"],
            top_clad_material=c["top_clad_material"],
            wavelength_nm=wl_nm,
            film_height_um=c["film_height_um"],
            slab_height_um=c["slab_height_um"],
            sidewall_deg=c["sidewall_deg"],
            ring_width_um=c["ring_width_um"],
            bus_width_um=c["bus_width_um"],
            ring_radius_um=c["ring_radius_um"],
            gap_thru_um=c["gap_thru_um"],
            gap_drop_um=c["gap_thru_um"] + 0.04,
            straight_length_um=c["straight_length_um"],
            pulley_angle_thru_deg=c["pulley_angle_thru_deg"],
            span_nm=max(2.5, round(12.0 * ((wl_nm / 1550.0) ** 1.8), 1)),
        )
        mrr = simulate_mrr_topology(cfg)
        gds_path = export_mrr_gds(cfg, gds_dir / f"{c['case_id']}.gds")

        neff_fem = float(np.real(m_fem.n_eff))
        neff_fde = float(np.real(m_fde.n_eff))
        diff_neff = abs(neff_fem - neff_fde)

        row = {
            "case_id": c["case_id"],
            "wavelength_nm": wl_nm,
            "bend_radius_um": c["ring_radius_um"],
            "neff_bsd_fem": round(neff_fem, 6),
            "neff_yee_fde": round(neff_fde, 6),
            "abs_diff_neff": round(diff_neff, 6),
            "ng_microring": mrr["metrics"]["ng_ring"],
            "FSR_nm_microring": mrr["metrics"]["FSR_nm"],
            "kappa_power_thru_cmt": mrr["metrics"]["kappa_power_thru"],
            "Q_ext_thru_cmt": mrr["metrics"]["Q_ext_thru"],
            "cc_param": mrr["critical_coupling"]["parameter"],
            "cc_target_val": mrr["critical_coupling"]["recommended_value"],
        }
        rows.append(row)

        exported_cases.append({
            **c,
            "gds_file": f"gds/{Path(gds_path).name}",
            "domain_width_um": round(dom_w, 3),
            "box_pad_um": round(box_pad, 3),
            "fde_dl_um": fde_dl,
            "n_core_xyz": [round(mc.nx, 6), round(mc.ny, 6), round(mc.nz, 6)],
            "n_clad": round(mcl.nx, 6),
            "n_top": round(mtp.nx, 6),
            "microring_reference": row,
        })
        print(
            f"[{c['case_id']:<26}] wl={wl_nm:6.1f} nm | FEM={neff_fem:.6f} | "
            f"FDE={neff_fde:.6f} | |d_neff|={diff_neff:.2e} | kappa^2={row['kappa_power_thru_cmt']:.4f}"
        )

    # Save CSV with solver provenance header & physical unit column names
    csv_path = OUT_DIR / "microring_vs_fde_multiband.csv"
    header_cols = (
        "case_id,wavelength_nm,bend_radius_um,neff_bsd_fem,neff_yee_fde,abs_diff_neff,"
        "ng_microring,FSR_nm_microring,kappa_power_thru_cmt,Q_ext_thru_cmt,cc_target_val"
    )
    host_tag = f"{platform.system()}-{platform.machine()} (Python {platform.python_version()})"
    lines = [
        f"# Host={host_tag} | MicroRing BSD Conformal FEM vs Tidy3D Yee-Grid FDE",
        header_cols,
    ]
    for r in rows:
        lines.append(
            f"{r['case_id']},{r['wavelength_nm']},{r['bend_radius_um']},{r['neff_bsd_fem']},"
            f"{r['neff_yee_fde']},{r['abs_diff_neff']},{r['ng_microring']},{r['FSR_nm_microring']},"
            f"{r['kappa_power_thru_cmt']},{r['Q_ext_thru_cmt']},{r['cc_target_val']}"
        )
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    (OUT_DIR / "lumerical_cases.json").write_text(
        json.dumps(exported_cases, indent=2), encoding="utf-8"
    )

    # Save Markdown Verification Report
    md = [
        "# Multi-Waveband Cross-Solver Verification Report (Visible -> 1310 -> 1550 -> Mid-IR)",
        "",
        f"- **Host**: `{host_tag}` (`{time.perf_counter() - t0:.1f} s` wall-clock)",
        "- **Solvers Compared Locally**:",
        "  1. `MicroRing Conformal Vector FEM` (`scikit-fem` 2nd-order `N2/P2`, zero-GPL BSD Delaunay mesher)",
        "  2. `Tidy3D Local CPU Yee-Grid FDE` (structured Yee finite-difference eigenmode discretization)",
        "- **Scope Boundary**: This report verifies 2D bent Maxwell eigenmode agreement (`|Delta n_eff|`) across 5 wavebands (`532 nm` to `4200 nm`). Full commercial Ansys Lumerical `MODE FDE` + `3D FDTD` coupler S-parameter (`S21`/`S31`) validation is executed on a Lumerical-equipped workstation via `run_lumapi_validation.py`.",
        "",
        "| Case ID | $\\lambda$ (nm) | $R$ (um) | $n_{\\mathrm{eff}}$ (BSD FEM) | $n_{\\mathrm{eff}}$ (Yee FDE) | $|\\Delta n_{\\mathrm{eff}}|$ | $n_g$ | FSR (nm) | $\\kappa^2$ (CMT) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in rows:
        md.append(
            f"| `{r['case_id']}` | {r['wavelength_nm']:.1f} | {r['bend_radius_um']:.1f} | "
            f"{r['neff_bsd_fem']:.6f} | {r['neff_yee_fde']:.6f} | `{r['abs_diff_neff']:.2e}` | "
            f"{r['ng_microring']:.4f} | {r['FSR_nm_microring']:.3f} | {r['kappa_power_thru_cmt']:.4f} |"
        )
    (OUT_DIR / "LOCAL_CROSSCHECK_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nSaved {csv_path} and {OUT_DIR / 'LOCAL_CROSSCHECK_REPORT.md'}")


if __name__ == "__main__":
    main()
