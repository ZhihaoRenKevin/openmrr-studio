"""Token-Minimal Local-Compute Tooling for AI Agents (`Codex`, `Claude`, `Antigravity`, `Ollama`).

Design philosophy:
  1. **100% Local Physics Execution**: 2D vector FEM eigenmodes (with persistent SSD mode
     caching), spatial pulley/point/racetrack CMT integrals, GPU/AMX/CPU broadband TMM
     spectra, GDSII polygon extraction, and BIC curve fitting run entirely on local hardware.
  2. **Zero Array Dumping (<150 Tokens per Call)**: Large arrays (`wavelength_nm`, `thru_dB`,
     2D mode fields, GDS vertex lists) are written to local `.csv`/`.gds` files under
     `outputs/agent_runs/`, while stdout / MCP returns ONLY compact scalar KPIs + file paths.
"""
from __future__ import annotations

from dataclasses import fields, replace
import math
import os
from pathlib import Path
import time

import numpy as np

from .active_tuning import export_lumerical_interconnect_bundle, run_active_tuning_analysis
from .fab_tolerance import export_fab_bias_array_gds, run_fabrication_error_analysis
from .gds_bridge import (
    analyze_uploaded_gds,
    export_sweep_array_gds,
    write_klayout_layer_props,
)
from .hardware_accel import detect_hardware_profile, run_compute_benchmark
from .materials import C0_M_PER_S, MATERIAL_CATALOG
from .mrr_cmt_fit_predict import fit_multi_resonance_spectrum, fit_single_resonance_cmt
from .mrr_topologies import (
    MRRDesignConfig,
    TOPOLOGY_CATALOG,
    export_mrr_gds,
    get_default_output_root,
    simulate_mrr_topology,
)
from .sweeps import run_mrr_parameter_sweep, run_waveguide_width_sweep

AGENT_OUT_DIR = Path(os.environ.get("OPENMRR_AGENT_OUT", str(get_default_output_root() / "agent_runs")))


def _cfg_from_dict(d: dict) -> MRRDesignConfig:
    valid = {f.name for f in fields(MRRDesignConfig)}
    aliases = {
        "mat": "core_material",
        "material": "core_material",
        "clad": "clad_material",
        "top_clad": "top_clad_material",
        "top": "topology",
        "h_um": "film_height_um",
        "slab_um": "slab_height_um",
        "w_ring_um": "ring_width_um",
        "w_bus_um": "bus_width_um",
        "r_um": "ring_radius_um",
        "r2_um": "ring2_radius_um",
        "gap_um": "gap_thru_um",
        "ls_um": "straight_length_um",
        "theta_deg": "pulley_angle_thru_deg",
        "wl_nm": "wavelength_nm",
        "pol": "polarization",
        "loss_db_cm": "alpha_loss_db_per_cm",
        "dt_k": "delta_temp_k",
    }
    mapped: dict = {}
    for k, v in d.items():
        if v is None:
            continue
        target_k = aliases.get(k, k)
        if target_k in valid:
            mapped[target_k] = v
    if "gap_thru_um" in mapped and "gap_drop_um" not in mapped:
        mapped["gap_drop_um"] = mapped["gap_thru_um"]
    return MRRDesignConfig(**mapped)


def agent_status() -> dict:
    """Return compact local compute profile + valid material/topology identifiers (~90 tokens)."""
    hw = detect_hardware_profile()
    bench = run_compute_benchmark(50_000)
    return {
        "os": f"{hw.os_name}-{hw.arch}",
        "backend": hw.selected_spectrum_backend,
        "cores": hw.physical_cores,
        "ram_avail_gb": hw.ram_available_gb,
        "cuda_gpu": hw.cuda_device_name,
        "tmm_mpts_s": bench["throughput_mpts_per_s"],
        "materials": list(MATERIAL_CATALOG.keys()),
        "topologies": list(TOPOLOGY_CATALOG.keys()),
    }


def agent_width_cutoff(params: dict) -> dict:
    """Run local 2D FEM waveguide width sweep; save full CSV locally, return compact cutoff KPIs."""
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    mat = str(params.get("core_material") or params.get("mat") or "Si3N4")
    pol = str(params.get("polarization") or params.get("pol") or "TE0")
    h_um = float(params.get("film_height_um") or params.get("h_um") or 0.40)
    slab_um = float(params.get("slab_height_um") or params.get("slab_um") or 0.0)
    sw_deg = float(params.get("sidewall_deg") or 85.0)
    wl_nm = float(params.get("wavelength_nm") or params.get("wl_nm") or 1550.0)
    w_min = float(params.get("w_min_um") or 0.50)
    w_max = float(params.get("w_max_um") or 2.00)
    n_pts = int(params.get("num_points") or 7)
    top_clad = str(params.get("top_clad_material") or "SiO2")
    clad = str(params.get("clad_material") or "SiO2")

    res = run_waveguide_width_sweep(
        core_material=mat,
        clad_material=clad,
        top_clad_material=top_clad,
        h_film_um=h_um,
        h_slab_um=slab_um,
        sidewall_deg=sw_deg,
        wavelength_nm=wl_nm,
        w_min_um=w_min,
        w_max_um=w_max,
        num_points=n_pts,
        polarization=pol,
    )
    csv_path = AGENT_OUT_DIR / f"width_sweep_{mat}_{pol}.csv"
    ho_clean = [np.nan if v is None else v for v in res["neff_higher_order"]]
    np.savetxt(
        csv_path,
        np.column_stack([
            res["widths_um"],
            res["neff_fundamental"],
            res["ng_fundamental"],
            ho_clean,
            res["core_confinement"],
        ]),
        delimiter=",",
        header="width_um,neff_fund,ng_fund,neff_higher_order,core_confinement",
        comments="",
    )
    idx_rec = int(np.argmin(np.abs(np.asarray(res["widths_um"]) - res["recommended_ring_width_um"])))
    return {
        "mat": mat,
        "pol": pol,
        "sm_max_w_um": res["single_mode_max_width_um"],
        "rec_w_bus_um": res["recommended_bus_width_um"],
        "rec_w_ring_um": res["recommended_ring_width_um"],
        "neff_at_rec": res["neff_fundamental"][idx_rec],
        "ng_at_rec": res["ng_fundamental"][idx_rec],
        "csv": str(csv_path),
    }


def agent_design_mrr(params: dict) -> dict:
    """Synthesize MRR locally (optional target FSR, 1-click critical coupling & GDS export)."""
    t0 = time.perf_counter()
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _cfg_from_dict(params)

    # Optional: auto-solve radius R for requested target_fsr_ghz
    target_fsr_ghz = params.get("target_fsr_ghz")
    if target_fsr_ghz:
        scout = simulate_mrr_topology(replace(cfg, num_spectrum_points=256))
        ng = float(scout["metrics"]["ng_ring"])
        l_rt_m = C0_M_PER_S / (ng * float(target_fsr_ghz) * 1e9)
        ls_um = cfg.straight_length_um if cfg.topology.startswith("racetrack") else 0.0
        r_solved = max(5.0, round((l_rt_m * 1e6 - 2.0 * ls_um) / (2.0 * math.pi), 3))
        cfg = replace(cfg, ring_radius_um=r_solved)

    res = simulate_mrr_topology(cfg)
    if params.get("apply_cc"):
        cc_info = res["critical_coupling"]
        p_cc = cc_info["parameter"]
        cfg = replace(cfg, **{p_cc: float(cc_info["recommended_value"])})
        res = simulate_mrr_topology(cfg)

    m = res["metrics"]
    cc = res["critical_coupling"]
    sp = res["spectrum"]
    tag = f"{cfg.topology}_{cfg.core_material}_R{cfg.ring_radius_um:.1f}"
    csv_path = AGENT_OUT_DIR / f"spec_{tag}.csv"
    np.savetxt(
        csv_path,
        np.column_stack([sp["wavelength_nm"], sp["thru_dB"], sp["drop_dB"]]),
        delimiter=",",
        header="wavelength_nm,thru_dB,drop_dB",
        comments="",
    )

    out = {
        "top": cfg.topology,
        "mat": cfg.core_material,
        "R_um": cfg.ring_radius_um,
        "W_ring_um": cfg.ring_width_um,
        "W_bus_um": cfg.bus_width_um,
        "gap_um": cfg.gap_thru_um,
        "loss_dB_cm": round(m["alpha_loss_db_per_cm"], 3),
        "neff": round(m["neff_ring"], 5),
        "ng": round(m["ng_ring"], 5),
        "FSR_GHz": round(m["FSR_GHz"], 2),
        "FSR_nm": round(m["FSR_nm"], 4),
        "Q_L": int(m["Q_loaded"]),
        "Q_int": int(m["Q_int"]),
        "Q_ext": int(m["Q_ext_thru"]),
        "ER_dB": round(m["ER_thru_dB"], 2),
        "regime": cc["regime"],
        "cc_param": cc["parameter"],
        "cc_val": cc["recommended_value"],
        "ms": round((time.perf_counter() - t0) * 1e3, 1),
        "csv": str(csv_path),
    }
    if abs(float(m.get("tuning_shift_pm", 0.0))) > 1e-6:
        out["shift_pm"] = round(m["tuning_shift_pm"], 2)
    if params.get("export_gds"):
        gds_path = export_mrr_gds(cfg, AGENT_OUT_DIR / f"{tag}.gds")
        write_klayout_layer_props(Path(gds_path).with_suffix(".lyp"))
        out["gds"] = gds_path
    return out


def agent_sweep_mrr(params: dict) -> dict:
    """Run local multi-point MRR sweep (cached 2D FEM modes); save CSV/GDS locally, return compact best point."""
    t0 = time.perf_counter()
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _cfg_from_dict(params)
    p_name = str(params.get("param_name") or TOPOLOGY_CATALOG[cfg.topology]["coupler_param"])
    if "values" in params and params["values"]:
        vals = [float(x) for x in params["values"]]
    else:
        vmin = float(params.get("v_min", 0.16))
        vmax = float(params.get("v_max", 0.32))
        n_pts = int(params.get("num_points", 7))
        vals = [round(float(x), 4) for x in np.linspace(vmin, vmax, max(2, n_pts))]

    sw = run_mrr_parameter_sweep(cfg, p_name, vals)
    csv_path = AGENT_OUT_DIR / f"sweep_{cfg.core_material}_{p_name}.csv"
    np.savetxt(
        csv_path,
        np.column_stack([sw["values"], sw["ER_thru_dB"], sw["Q_loaded"], sw["resonance_shift_pm"]]),
        delimiter=",",
        header=f"{p_name}_{sw['unit']},ER_thru_dB,Q_loaded,resonance_shift_pm",
        comments="",
    )
    out = {
        "param": p_name,
        "unit": sw["unit"],
        "n_pts": len(vals),
        "range": [vals[0], vals[-1]],
        "best_val": sw["best_extinction_value"],
        "best_ER_dB": sw["best_extinction_dB"],
        "Q_L_at_best": int(sw["Q_loaded"][sw["best_critical_coupling_index"]]),
        "shift_span_pm": [sw["resonance_shift_pm"][0], sw["resonance_shift_pm"][-1]],
        "ms": round((time.perf_counter() - t0) * 1e3, 1),
        "csv": str(csv_path),
    }
    if params.get("export_array_gds"):
        arr_gds = export_sweep_array_gds(cfg, p_name, vals, AGENT_OUT_DIR / f"array_{cfg.core_material}_{p_name}.gds")
        out["array_gds"] = arr_gds
    return out


def agent_inspect_gds(params: dict) -> dict:
    """Extract MRR topology & dimensions from a local `.gds`/`.oas` without dumping polygon vertices."""
    gds_path = str(params["gds_path"])
    lyr = params.get("core_layer")
    core_tuple = (int(lyr[0]), int(lyr[1])) if lyr else None
    info = analyze_uploaded_gds(gds_path, core_layer=core_tuple, cell_name=params.get("cell_name"))
    return {
        "file": info["file_name"],
        "cell": info["cell_name"],
        "core_layer": info["selected_core_layer"],
        "bbox_um": info["bbox_um"],
        "extracted": info["extracted_geometry"],
    }


def agent_fit_spectrum(params: dict) -> dict:
    """Fit a local experimental `.csv`/`.txt` transmission trace via CMT without loading trace into LLM context."""
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_in = Path(str(params["csv_path"]))
    raw = np.genfromtxt(csv_in, delimiter="," if csv_in.suffix.lower() == ".csv" else None, comments="#")
    if raw.ndim != 2 or raw.shape[1] < 2:
        # Handle header row gracefully
        raw = np.genfromtxt(csv_in, delimiter="," if csv_in.suffix.lower() == ".csv" else None, skip_header=1)
    mask = np.isfinite(raw[:, 0]) & np.isfinite(raw[:, 1])
    wl, tr = raw[mask, 0], raw[mask, 1]
    if np.min(tr) < 0.0:
        # Auto-convert dB transmission to linear power if user passed dB CSV
        tr = 10.0 ** (tr / 10.0)

    model_type = str(params.get("model_type") or "auto")
    regime = params.get("known_regime") or None
    l_rt = float(params.get("ring_length_um") or 250.0)
    ng_in = float(params.get("ng") or params.get("ng_assumed") or 2.10)
    if model_type == "multi_fsr":
        m_res = fit_multi_resonance_spectrum(wl, tr, ring_length_um=l_rt, known_regime=regime)
        return {
            "mode": "multi_fsr",
            "n_peaks": m_res["num_resonances"],
            "FSR_GHz": round(m_res["mean_fsr_ghz"], 3),
            "FSR_nm": round(m_res["mean_fsr_nm"], 4),
            "ng_extracted": round(m_res["ng_extracted"], 5) if m_res["ng_extracted"] else None,
            "mean_Q_L": int(m_res["mean_Q_loaded"]),
            "mean_Q_int": int(m_res["mean_Q_int"]),
            "loss_dB_cm": m_res["alpha_loss_db_per_cm"],
        }

    s, y_fit, _ = fit_single_resonance_cmt(
        wl, tr, model_type=model_type, known_regime=regime, ng_assumed=ng_in, ring_length_um=l_rt
    )
    fit_csv = AGENT_OUT_DIR / f"fitted_{csv_in.stem}.csv"
    np.savetxt(
        fit_csv,
        np.column_stack([wl, tr, y_fit]),
        delimiter=",",
        header="wavelength_nm,measured_linear,cmt_fit_linear",
        comments="",
    )
    return {
        "model": s.model_type,
        "lambda0_nm": round(s.lambda0_nm, 5),
        "FWHM_pm": round(s.fwhm_pm, 3),
        "Q_L": int(s.Q_loaded),
        "Q_int": int(s.Q_int),
        "Q_ext": int(s.Q_ext),
        "loss_dB_cm": round(s.alpha_loss_db_per_cm, 4),
        "loss_under_dB_cm": s.alpha_loss_under_db_per_cm,
        "loss_over_dB_cm": s.alpha_loss_over_db_per_cm,
        "ng_used": s.ng_used,
        "ER_dB": round(s.extinction_ratio_db, 2),
        "split_2g_ghz": round(2.0 * s.mu_split_ghz, 4),
        "regime": s.coupling_regime_status,
        "r2": round(s.r_squared, 5),
        "fit_csv": str(fit_csv),
    }


def agent_fab_tolerance(params: dict) -> dict:
    """Run lithography exposure dose / photoresist-tone / CD-bias error analysis (<150 tokens)."""
    t0 = time.perf_counter()
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _cfg_from_dict(params)
    if params.get("apply_cc"):
        scout = simulate_mrr_topology(cfg)
        cc_info = scout["critical_coupling"]
        cfg = replace(cfg, **{cc_info["parameter"]: float(cc_info["recommended_value"])})

    resist = str(params.get("resist_tone") or params.get("resist") or "positive_pr")
    dose_pct = float(params.get("max_dose_error_pct") or params.get("dose_pct") or 15.0)
    slope = params.get("dose_slope_nm_per_pct") or params.get("slope_nm_pct")
    cd_nm = float(params.get("max_cd_bias_nm") or params.get("cd_nm") or 30.0)
    prox = params.get("proximity_gap_factor") or params.get("prox")
    dh_nm = float(params.get("delta_h_film_nm") or params.get("dh_nm") or 0.0)
    n_pts = int(params.get("num_points") or 7)

    fab = run_fabrication_error_analysis(
        cfg,
        resist_tone=resist,
        max_dose_error_pct=dose_pct,
        dose_slope_nm_per_pct=float(slope) if slope is not None else None,
        max_cd_bias_nm=cd_nm,
        proximity_gap_factor=float(prox) if prox is not None else None,
        delta_h_film_nm=dh_nm,
        num_points=n_pts,
    )
    corners = fab["corners"]
    csv_path = AGENT_OUT_DIR / f"fab_{cfg.core_material}_{resist}.csv"
    np.savetxt(
        csv_path,
        np.column_stack([
            [c["dose_error_pct"] for c in corners],
            [c["delta_cd_nm"] for c in corners],
            [c["w_ring_fab_um"] for c in corners],
            [c["gap_fab_um"] for c in corners],
            [c["extinction_ratio_dB"] for c in corners],
            [c["Q_loaded"] for c in corners],
            [c["delta_wl_res_nm"] for c in corners],
        ]),
        delimiter=",",
        header="dose_error_pct,delta_cd_nm,w_ring_fab_um,gap_fab_um,ER_dB,Q_loaded,delta_wl_res_nm",
        comments="",
    )
    s = fab["summary"]
    out = {
        "resist": fab["resist_tone"],
        "nom_ER_dB": s["nominal_er_dB"],
        "under_dose": {
            "dose_pct": s["under_dose_corner"]["dose_error_pct"],
            "dCD_nm": s["under_dose_corner"]["delta_cd_nm"],
            "gap_nm": round(s["under_dose_corner"]["gap_fab_um"] * 1e3, 1),
            "ER_dB": s["under_dose_corner"]["extinction_ratio_dB"],
            "dwl_nm": s["under_dose_corner"]["delta_wl_res_nm"],
            "regime": s["under_dose_corner"]["coupling_regime"],
        },
        "over_dose": {
            "dose_pct": s["over_dose_corner"]["dose_error_pct"],
            "dCD_nm": s["over_dose_corner"]["delta_cd_nm"],
            "gap_nm": round(s["over_dose_corner"]["gap_fab_um"] * 1e3, 1),
            "ER_dB": s["over_dose_corner"]["extinction_ratio_dB"],
            "dwl_nm": s["over_dose_corner"]["delta_wl_res_nm"],
            "regime": s["over_dose_corner"]["coupling_regime"],
        },
        "cd_win_ER15_nm": s["cd_window_er15_nm"],
        "dose_win_ER15_pct": s["dose_window_er15_pct"],
        "dl_dCD_pm_nm": s["sensitivity_dl_dcd_pm_per_nm"],
        "ms": round((time.perf_counter() - t0) * 1e3, 1),
        "csv": str(csv_path),
    }
    if params.get("export_bias_gds"):
        gds_info = export_fab_bias_array_gds(
            cfg,
            AGENT_OUT_DIR / f"opc_bias_array_{cfg.core_material}_{cfg.topology}.gds",
            proximity_gap_factor=fab["proximity_gap_factor"],
        )
        out["bias_gds"] = gds_info["gds_path"]
    return out


def agent_active_tuning(params: dict) -> dict:
    """Run 2D-FEM active tuning (TO/EO/Si-PN/Si-PIN + T/E/V/I sweeps) & optional INTERCONNECT export (<150 tokens)."""
    t0 = time.perf_counter()
    AGENT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _cfg_from_dict(params)
    if params.get("apply_cc"):
        scout = simulate_mrr_topology(cfg)
        cc_info = scout["critical_coupling"]
        cfg = replace(cfg, **{cc_info["parameter"]: float(cc_info["recommended_value"])})

    raw_b = params.get("bias_values") or params.get("biases")
    bias_list: list[float] | None = None
    if isinstance(raw_b, str) and raw_b.strip():
        bias_list = [float(x.strip()) for x in raw_b.split(",") if x.strip()]
    elif isinstance(raw_b, (list, tuple)) and len(raw_b) > 0:
        bias_list = [float(x) for x in raw_b]

    mech = str(params.get("mechanism") or "auto")
    drv = str(params.get("drive_type") or params.get("drive") or "auto")

    tune = run_active_tuning_analysis(
        cfg,
        mechanism=mech,
        drive_type=drv,
        bias_values=bias_list,
        active_fraction=float(params.get("active_fraction") or 0.78),
        heater_material=str(params.get("heater_material") or "TiN"),
        heater_width_um=float(params.get("heater_width_um") or 1.60),
        heater_gap_um=float(params.get("heater_gap_um") or 0.90),
        box_thickness_um=float(params.get("box_thickness_um") or 2.00),
        electrode_gap_um=float(params["electrode_gap_um"]) if params.get("electrode_gap_um") is not None else None,
        na_p_cm3=float(params.get("na_p_cm3") or 5.0e17),
        nd_n_cm3=float(params.get("nd_n_cm3") or 5.0e17),
        pn_offset_nm=float(params.get("pn_offset_nm") or 25.0),
        heavy_contact_offset_um=float(params.get("heavy_contact_offset_um") or 0.85),
    )

    eff = tune["efficiency"]
    states = tune["states"]
    csv_path = AGENT_OUT_DIR / f"tuning_{cfg.core_material}_{eff['mechanism']}.csv"
    np.savetxt(
        csv_path,
        np.column_stack([
            [s["bias_value"] for s in states],
            [s["delta_neff_active_real"] for s in states],
            [s["alpha_active_db_per_cm"] for s in states],
            [s["delta_wl_pm"] for s in states],
            [s["ER_thru_dB"] for s in states],
        ]),
        delimiter=",",
        header=f"bias_{eff['drive_unit']},delta_neff_active_real,alpha_active_dB_per_cm,delta_wl_pm,ER_thru_dB",
        comments="",
    )

    out = {
        "mech": eff["mechanism"],
        "drive": f"{eff['drive_type']}[{eff['drive_unit']}]",
        "slope": f"{eff['primary_slope']} {eff['primary_slope_unit']}",
        "freq_slope": f"{eff['freq_slope']} {eff['freq_slope_unit']}",
        "pi_fom": f"{eff['pi_figure']} {eff['pi_figure_unit']}",
        "bw_3dB": f"{eff['bandwidth_3db']} {eff['bandwidth_unit']}" if eff.get("bandwidth_3db") else None,
        "dwl_span_pm": [states[0]["delta_wl_pm"], states[-1]["delta_wl_pm"]],
        "loss_span_dB_cm": [states[0]["alpha_active_db_per_cm"], states[-1]["alpha_active_db_per_cm"]],
        "ms": round((time.perf_counter() - t0) * 1e3, 1),
        "csv": str(csv_path),
    }
    if params.get("export_interconnect"):
        ic = export_lumerical_interconnect_bundle(
            cfg,
            tune,
            AGENT_OUT_DIR / f"interconnect_{cfg.core_material}_{eff['mechanism']}",
            make_zip=True,
        )
        out["interconnect_zip"] = ic["zip_path"]
    return out

