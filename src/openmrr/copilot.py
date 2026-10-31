"""Conversational Photonics Design Copilot (`openmrr.copilot`).

Guides users step-by-step from application requirements -> wafer stack -> 2D Maxwell
eigenmode & single-mode cutoff check -> resonator & coupler synthesis -> parameter sweeps
-> foundry GDSII mask creation or uploaded-GDS optical verification.

Works 100% offline with deterministic physics-grounded natural-language parsing
(English & Simplified Chinese), with optional local Ollama (`127.0.0.1:11434`) commentary.
"""
from __future__ import annotations

from dataclasses import asdict, fields, replace
import json
import math
from pathlib import Path
import re
import urllib.request

import numpy as np

from .eigenmode_solver import WaveguideCrossSectionSpec, solve_modes_fem
from .gds_bridge import (
    analyze_uploaded_gds,
    export_sweep_array_gds,
    write_klayout_layer_props,
)
from .materials import C0_M_PER_S, MATERIAL_CATALOG, T_REF_K, get_material_fn
from .mrr_topologies import (
    MRRDesignConfig,
    TOPOLOGY_CATALOG,
    export_mrr_gds,
    simulate_mrr_topology,
)
from .sweeps import run_mrr_parameter_sweep, run_waveguide_width_sweep

# Foundry-standard starting presets per core material so beginners get physical defaults immediately
PLATFORM_PRESETS: dict[str, dict] = {
    "Si": {
        "film_height_um": 0.22,
        "slab_height_um": 0.0,
        "sidewall_deg": 86.0,
        "ring_width_um": 0.50,
        "bus_width_um": 0.45,
        "ring_radius_um": 20.0,
        "gap_thru_um": 0.18,
        "gap_drop_um": 0.18,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.30, 0.85),
    },
    "a-Si": {
        "film_height_um": 0.25,
        "slab_height_um": 0.0,
        "sidewall_deg": 85.0,
        "ring_width_um": 0.52,
        "bus_width_um": 0.46,
        "ring_radius_um": 25.0,
        "gap_thru_um": 0.20,
        "gap_drop_um": 0.20,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.32, 0.90),
    },
    "Si3N4": {
        "film_height_um": 0.40,
        "slab_height_um": 0.0,
        "sidewall_deg": 85.0,
        "ring_width_um": 1.20,
        "bus_width_um": 1.00,
        "ring_radius_um": 50.0,
        "gap_thru_um": 0.25,
        "gap_drop_um": 0.25,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.60, 2.10),
    },
    "SiRich_SiNx": {
        "film_height_um": 0.35,
        "slab_height_um": 0.0,
        "sidewall_deg": 84.0,
        "ring_width_um": 0.90,
        "bus_width_um": 0.75,
        "ring_radius_um": 35.0,
        "gap_thru_um": 0.22,
        "gap_drop_um": 0.22,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.45, 1.50),
    },
    "4H-SiC": {
        "film_height_um": 0.60,
        "slab_height_um": 0.0,
        "sidewall_deg": 82.0,
        "ring_width_um": 1.10,
        "bus_width_um": 0.85,
        "ring_radius_um": 40.0,
        "gap_thru_um": 0.22,
        "gap_drop_um": 0.22,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.45, 1.70),
    },
    "3C-SiC": {
        "film_height_um": 0.55,
        "slab_height_um": 0.0,
        "sidewall_deg": 82.0,
        "ring_width_um": 1.05,
        "bus_width_um": 0.85,
        "ring_radius_um": 40.0,
        "gap_thru_um": 0.22,
        "gap_drop_um": 0.22,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.45, 1.65),
    },
    "AlN": {
        "film_height_um": 0.80,
        "slab_height_um": 0.20,
        "sidewall_deg": 78.0,
        "ring_width_um": 1.20,
        "bus_width_um": 1.00,
        "ring_radius_um": 60.0,
        "gap_thru_um": 0.25,
        "gap_drop_um": 0.25,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.60, 2.00),
    },
    "ScAlN_20": {
        "film_height_um": 0.60,
        "slab_height_um": 0.15,
        "sidewall_deg": 76.0,
        "ring_width_um": 1.15,
        "bus_width_um": 0.95,
        "ring_radius_um": 55.0,
        "gap_thru_um": 0.24,
        "gap_drop_um": 0.24,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.55, 1.90),
    },
    "LN_Xcut": {
        "topology": "racetrack_ap",
        "film_height_um": 0.60,
        "slab_height_um": 0.30,
        "sidewall_deg": 70.0,
        "ring_width_um": 1.40,
        "bus_width_um": 1.20,
        "ring_radius_um": 80.0,
        "straight_length_um": 30.0,
        "gap_thru_um": 0.30,
        "gap_drop_um": 0.30,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.75, 2.30),
    },
    "LN_Zcut": {
        "film_height_um": 0.60,
        "slab_height_um": 0.30,
        "sidewall_deg": 70.0,
        "ring_width_um": 1.40,
        "bus_width_um": 1.20,
        "ring_radius_um": 80.0,
        "gap_thru_um": 0.28,
        "gap_drop_um": 0.28,
        "clad_material": "SiO2",
        "top_clad_material": "SiO2",
        "wavelength_nm": 1550.0,
        "w_sweep": (0.75, 2.30),
    },
    "Ge": {
        "film_height_um": 1.40,
        "slab_height_um": 0.30,
        "sidewall_deg": 82.0,
        "ring_width_um": 2.10,
        "bus_width_um": 1.80,
        "ring_radius_um": 65.0,
        "gap_thru_um": 0.35,
        "gap_drop_um": 0.35,
        "clad_material": "Al2O3",
        "top_clad_material": "Air",
        "wavelength_nm": 4200.0,
        "span_nm": 35.0,
        "w_sweep": (1.10, 3.20),
    },
}


def create_initial_session() -> dict:
    """Create a fresh Conversational Photonics Copilot session dictionary."""
    cfg = asdict(MRRDesignConfig())
    welcome = (
        "Welcome to **OpenMRR Copilot** — your license-free Maxwell eigenmode & CMT microring designer.\n\n"
        "Tell me your target platform or application (or **upload a `.gds` file** to extract and simulate it):\n"
        "- **Step 1**: Core material & wafer stack (`H_film`, `H_slab`, cladding, sidewall)\n"
        "- **Step 2**: Polarization (`TE0`/`TM0`) & single-mode waveguide width check\n"
        "- **Step 3**: Topology (`Circular`, `Racetrack`, `Pulley`, `Vernier`) & target `FSR` / `Q` / sweeps -> `.gds` mask"
    )
    return {
        "stage": "welcome",
        "config": cfg,
        "confirmed": [],
        "target_fsr_ghz": None,
        "target_fsr_nm": None,
        "last_width_sweep": None,
        "last_mrr_metrics": None,
        "history": [{"role": "assistant", "content": welcome}],
    }


def get_welcome_chips() -> list[dict[str, str]]:
    """Starter quick-reply chips shown when a user opens the Copilot."""
    return [
        {"label": "220 nm SOI (TE0, 1550 nm)", "prompt": "Design on 220 nm SOI, strip waveguide, SiO2 clad, TE0 at 1550 nm"},
        {"label": "400 nm Si3N4 Low-Loss", "prompt": "400 nm Si3N4 strip waveguide, SiO2 clad, TE0 at 1550 nm"},
        {"label": "600 nm 4H-SiC Pulley MRR", "prompt": "600 nm 4H-SiC strip, SiO2 clad, TE0 at 1550 nm, pulley all-pass"},
        {"label": "600 nm X-cut TFLN EO Racetrack", "prompt": "600 nm X-cut TFLN with 300 nm slab, SiO2 clad, TE0 at 1550 nm, racetrack"},
        {"label": "800 nm ScAlN (20% Sc) Rib", "prompt": "800 nm ScAlN 20% with 200 nm slab, SiO2 clad, TE0 at 1550 nm"},
        {"label": "Mid-IR Ge @ 4.2 um", "prompt": "1400 nm Ge with 300 nm slab on Al2O3, air clad, TE0 at 4200 nm"},
    ]


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _to_um(value: float, unit: str) -> float:
    u = unit.lower().strip()
    if u in ("nm", "纳米"):
        return round(value * 1e-3, 4)
    return round(value, 4)


def parse_photonics_intent(message: str) -> dict:
    """Extract material, wafer stack, mode, topology, targets, and sweep/GDS actions from text."""
    text = message.strip()
    low = text.lower()
    out: dict = {
        "lang": "zh" if _has_cjk(text) else "en",
        "fields": {},
        "targets": {},
        "action": None,
        "sweep": None,
    }

    if re.search(r"\b(reset|start over|new design|clear session)\b|重置|重新开始|新建设计", low):
        out["action"] = "reset"
        return out

    # 1. Core Material Recognition (ordered from specific to general)
    mat = None
    if re.search(r"scaln|氮化铝钪", low):
        sc_match = re.search(r"(10|20|30)\s*%", low) or re.search(r"scaln[_\s]*(10|20|30)", low)
        pct = sc_match.group(1) if sc_match else "20"
        mat = f"ScAlN_{pct}"
        out["fields"]["sc_fraction"] = float(pct) / 100.0
    elif re.search(r"\b4h[-_\s]*sic\b|碳化硅|\bsic\b", low) and "3c" not in low:
        mat = "4H-SiC"
    elif re.search(r"\b3c[-_\s]*sic\b", low):
        mat = "3C-SiC"
    elif re.search(r"si[-_\s]*rich|srn|富硅氮化硅|sinx", low):
        mat = "SiRich_SiNx"
    elif re.search(r"\bsi3n4\b|\bsin\b|silicon nitride|氮化硅", low):
        mat = "Si3N4"
    elif re.search(r"\ba[-_\s]*si\b|amorphous silicon|非晶硅", low):
        mat = "a-Si"
    elif re.search(r"x[-_\s]*cut.*(ln|tfln|linbo3|niobate)|x切.*铌酸锂", low):
        mat = "LN_Xcut"
    elif re.search(r"z[-_\s]*cut.*(ln|tfln|linbo3|niobate)|z切.*铌酸锂", low):
        mat = "LN_Zcut"
    elif re.search(r"\b(tfln|linbo3|lithium niobate|ln)\b|铌酸锂", low):
        mat = "LN_Xcut"
    elif re.search(r"\baln\b|aluminum nitride|aluminium nitride|氮化铝", low):
        mat = "AlN"
    elif re.search(r"\bgsst\b|phase[-_\s]*change|相变", low):
        mat = "GSST_crystalline" if ("cryst" in low or "晶态" in low) else "GSST_amorphous"
    elif re.search(r"\bgermanium\b|\bge\b|锗", low):
        mat = "Ge"
    elif re.search(r"\bsoi\b|\bc-si\b|\bsilicon\b|\bsi\b|硅波导|绝缘体上硅", low):
        mat = "Si"

    if mat:
        out["fields"]["core_material"] = mat

    # 2. Cladding
    if re.search(r"air[-_\s]*(clad|top)|unclad|空气包层|无上包层", low):
        out["fields"]["top_clad_material"] = "Air"
    elif re.search(r"(sio2|oxide|silica)[-_\s]*(clad|top)|二氧化硅包层|氧化物包层", low):
        out["fields"]["top_clad_material"] = "SiO2"
        out["fields"]["clad_material"] = "SiO2"
    if re.search(r"on\s+al2o3|sapphire|蓝宝石基底", low):
        out["fields"]["clad_material"] = "Al2O3"

    # 3. Polarization
    if re.search(r"\btm0?\b|横磁", low):
        out["fields"]["polarization"] = "TM0"
    elif re.search(r"\bte0?\b|横电", low):
        out["fields"]["polarization"] = "TE0"

    # 4. Wavelength (e.g., "@ 1550 nm", "at 780 nm", "wavelength 1310 nm", "4.2 um")
    wl_m = (
        re.search(r"(?:wavelength|wl|lambda|@|\bat\b|波长)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
        or re.search(r"\b(736|750|780|850|980|1064|1310|1530|1550|2000|3800|4200)(?:\.\d+)?\s*(nm)\b", low)
    )
    if wl_m:
        val, unit = float(wl_m.group(1)), wl_m.group(2)
        wl_nm = val * 1000.0 if unit in ("um", "µm") else val
        if 380.0 <= wl_nm <= 12000.0:
            out["fields"]["wavelength_nm"] = round(wl_nm, 3)

    # 5. Film height H_film & Slab height H_slab & Sidewall angle
    # Pattern like "220 nm SOI", "400nm Si3N4", "600 nm 4H-SiC", "H_film = 500 nm", "film 0.4 um"
    h_explicit = re.search(
        r"(?:h_?film|film(?:\s*height|\s*thickness)?|thickness|core\s*height|膜厚|厚度)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)",
        low,
    )
    h_prefix = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(nm|um|µm)\s+(?:soi|si3n4|sin|4h-sic|3c-sic|sic|aln|scaln|x-cut|z-cut|tfln|ln|ge|a-si|si\b)",
        low,
    )
    if h_explicit:
        out["fields"]["film_height_um"] = _to_um(float(h_explicit.group(1)), h_explicit.group(2))
    elif h_prefix:
        h_val = _to_um(float(h_prefix.group(1)), h_prefix.group(2))
        if 0.05 <= h_val <= 5.0:
            out["fields"]["film_height_um"] = h_val

    if re.search(r"strip|full[-_\s]*etch|slab\s*[=:]?\s*0\b|条形波导|全刻蚀", low):
        out["fields"]["slab_height_um"] = 0.0
    else:
        slab_m = (
            re.search(r"(?:h_?slab|slab(?:\s*height|\s*thickness)?|平板层|剩余厚度)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
            or re.search(r"(\d+(?:\.\d+)?)\s*(nm|um|µm)\s+slab\b", low)
        )
        if slab_m:
            out["fields"]["slab_height_um"] = _to_um(float(slab_m.group(1)), slab_m.group(2))

    sw_m = (
        re.search(r"(?:sidewall|侧壁角?)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(?:deg|°|度)?", low)
        or re.search(r"(\d+(?:\.\d+)?)\s*(?:deg|°|度)\s*sidewall", low)
    )
    if sw_m:
        ang = float(sw_m.group(1))
        if 55.0 <= ang <= 90.0:
            out["fields"]["sidewall_deg"] = ang

    # 6. Sweep Commands (detect BEFORE generic single-value parameters so ranges aren't misread)
    sweep_match = re.search(
        r"(?:sweep|scan|vary|扫描|扫参|扫)\s*(width|w\b|gap|pulley|angle|theta|length|straight|l_s|radius|r\b|temp|temperature|voltage|bias|波导宽度|宽度|间距|包角|角度|直波导|耦合长度|半径|温度|电压)",
        low,
    )
    if sweep_match or re.search(r"single[-_\s]*mode\s*(?:check|sweep|cutoff|width)|单模(?:分析|截止|检查)", low):
        nums = [
            (float(m.group(1)), m.group(2))
            for m in re.finditer(r"(-?\d+(?:\.\d+)?)\s*(nm|um|µm|deg|°|k|v)?", low[sweep_match.end():] if sweep_match else low)
        ]
        kind_tok = sweep_match.group(1) if sweep_match else "width"
        if kind_tok in ("width", "w", "波导宽度", "宽度"):
            w_pair = [(_to_um(v, u) if u in ("nm", "um", "µm") else v) for v, u in nums if v > 0]
            out["action"] = "sweep_width"
            if len(w_pair) >= 2:
                out["sweep"] = {"w_min_um": min(w_pair[0], w_pair[1]), "w_max_um": max(w_pair[0], w_pair[1])}
            return out

        param_map = {
            "gap": "gap_thru_um",
            "间距": "gap_thru_um",
            "pulley": "pulley_angle_thru_deg",
            "angle": "pulley_angle_thru_deg",
            "theta": "pulley_angle_thru_deg",
            "包角": "pulley_angle_thru_deg",
            "角度": "pulley_angle_thru_deg",
            "length": "straight_length_um",
            "straight": "straight_length_um",
            "l_s": "straight_length_um",
            "直波导": "straight_length_um",
            "耦合长度": "straight_length_um",
            "radius": "ring_radius_um",
            "r": "ring_radius_um",
            "半径": "ring_radius_um",
            "temp": "delta_temp_k",
            "temperature": "delta_temp_k",
            "温度": "delta_temp_k",
            "voltage": "voltage_v",
            "bias": "voltage_v",
            "电压": "voltage_v",
        }
        p_name = param_map.get(kind_tok, "gap_thru_um")
        out["action"] = "sweep_mrr"
        vals_parsed = []
        for v, u in nums[:2]:
            if p_name.endswith("_um") and u == "nm":
                vals_parsed.append(v * 1e-3)
            elif p_name == "gap_thru_um" and u == "" and v > 10.0:
                vals_parsed.append(v * 1e-3)  # e.g., "sweep gap 150 to 350 nm" where first num lacked unit
            else:
                vals_parsed.append(v)
        out["sweep"] = {
            "param_name": p_name,
            "range": (vals_parsed[0], vals_parsed[1]) if len(vals_parsed) >= 2 else None,
        }
        return out

    # 7. Waveguide Widths, Radius, Gap, Pulley Angle, Straight Length, Loss, Active Tuning
    wr_m = re.search(r"(?:w_?ring|ring\s*width|环宽)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
    wb_m = re.search(r"(?:w_?bus|bus\s*width|总线宽)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
    wg_m = re.search(r"(?:\bwidth\b|波导宽)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
    if wr_m:
        out["fields"]["ring_width_um"] = _to_um(float(wr_m.group(1)), wr_m.group(2))
    if wb_m:
        out["fields"]["bus_width_um"] = _to_um(float(wb_m.group(1)), wb_m.group(2))
    if wg_m and not wr_m and not wb_m:
        w_u = _to_um(float(wg_m.group(1)), wg_m.group(2))
        out["fields"]["ring_width_um"] = w_u
        out["fields"]["bus_width_um"] = w_u

    rad_m = re.search(r"(?:\bradius\b|\br1?\s*=|半径)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(um|µm|nm)?", low)
    if rad_m:
        rv = float(rad_m.group(1))
        ru = rad_m.group(2) or "um"
        out["fields"]["ring_radius_um"] = _to_um(rv, ru)

    gap_m = re.search(r"(?:\bgap\b|间距)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(nm|um|µm)", low)
    if gap_m:
        gv = _to_um(float(gap_m.group(1)), gap_m.group(2))
        out["fields"]["gap_thru_um"] = gv
        out["fields"]["gap_drop_um"] = gv

    ang_m = re.search(r"(?:pulley\s*angle|wrap\s*angle|\btheta\b|包角)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(?:deg|°|度)?", low)
    if ang_m:
        out["fields"]["pulley_angle_thru_deg"] = float(ang_m.group(1))

    ls_m = re.search(r"(?:straight(?:\s*length)?|\bl_?s\b|直波导|耦合长度)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(um|µm|nm)", low)
    if ls_m:
        out["fields"]["straight_length_um"] = _to_um(float(ls_m.group(1)), ls_m.group(2))

    loss_m = re.search(r"(?:loss|\balpha\b|损耗)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*db\s*/\s*cm", low)
    if loss_m:
        out["fields"]["alpha_loss_db_per_cm"] = float(loss_m.group(1))

    dt_m = re.search(r"(?:delta_?t|\bdt\b|temp(?:erature)?|升温|温升)\s*[=:+]?\s*(-?\d+(?:\.\d+)?)\s*(?:k|°c|c\b)", low)
    if dt_m:
        out["fields"]["delta_temp_k"] = float(dt_m.group(1))

    volt_m = re.search(r"(?:voltage|bias|电压)\s*[=:]?\s*(-?\d+(?:\.\d+)?)\s*v\b", low)
    if volt_m:
        out["fields"]["voltage_v"] = float(volt_m.group(1))

    # 8. Target FSR
    fsr_m = re.search(r"\bfsr\b\s*(?:of|=|:|约|~)?\s*(\d+(?:\.\d+)?)\s*(ghz|thz|nm)", low)
    if fsr_m:
        f_val, f_unit = float(fsr_m.group(1)), fsr_m.group(2)
        if f_unit == "thz":
            out["targets"]["fsr_ghz"] = f_val * 1000.0
        elif f_unit == "ghz":
            out["targets"]["fsr_ghz"] = f_val
        elif f_unit == "nm":
            out["targets"]["fsr_nm"] = f_val

    # 9. Topology Selection
    is_ad = bool(re.search(r"add[-_\s]*drop|4[-_\s]*port|四端口|下载", low))
    is_ap = bool(re.search(r"all[-_\s]*pass|2[-_\s]*port|两端口|全通", low))
    if re.search(r"vernier|crow|dual[-_\s]*ring|双环|游标", low):
        out["fields"]["topology"] = "vernier_crow_ad"
    elif re.search(r"pulley|wrap[-_\s]*around|滑轮", low):
        out["fields"]["topology"] = "pulley_ad" if is_ad else "pulley_ap"
    elif re.search(r"racetrack|跑道", low):
        out["fields"]["topology"] = "racetrack_ad" if is_ad else "racetrack_ap"
    elif re.search(r"point|circular|圆环|点耦合", low):
        out["fields"]["topology"] = "point_circular_ad" if is_ad else "point_circular_ap"
    elif is_ad or is_ap:
        out["targets"]["ports"] = 4 if is_ad else 2

    # 10. Direct Action Triggers
    if re.search(r"critical[-_\s]*coupl|apply\s+cc|临界耦合", low):
        out["action"] = "apply_critical_coupling"
    elif re.search(r"(?:sweep|array).*gds|gds.*(?:sweep|array)|阵列.*(?:gds|版图)", low):
        out["action"] = "export_sweep_gds"
    elif re.search(r"(?:export|create|save|generate|download)\b.*(?:\.?\bgds\b|layout|mask)|(?:生成|导出|创建).*(?:gds|版图)", low):
        out["action"] = "export_single_gds"
    elif re.search(r"\b(simulate|calculate|compute|run\s+mrr|evaluate)\b|开始仿真|运行仿真|计算光谱|确认并仿真", low):
        out["action"] = "simulate_mrr"
    elif re.search(r"confirm\s+stack|check\s+mode|确认叠层", low):
        out["action"] = "sweep_width"

    return out


def _dict_to_cfg(cfg_dict: dict) -> MRRDesignConfig:
    valid = {f.name for f in fields(MRRDesignConfig)}
    return MRRDesignConfig(**{k: v for k, v in cfg_dict.items() if k in valid})


def _maybe_ollama_commentary(compact_kpi: str) -> str | None:
    """Zero-cloud-token local LLM tip via Ollama (`127.0.0.1:11434`) or LM Studio MLX (`127.0.0.1:1234`).

    Sends ONLY a <80-token scalar KPI summary and disables reasoning chains (`think: False`)
    so local inference finishes in <1 s on Apple Silicon / CUDA / NPU with minimal RAM/compute.
    """
    prompt = f"Give ONE 1-sentence practical photonics fab/design tip for this MRR: {compact_kpi}"

    # 1. Try local Ollama (auto-detect first installed chat model, prefer qwen3:14b / llama3)
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.8) as tag_resp:
            models = [m.get("name", "") for m in json.loads(tag_resp.read().decode("utf-8")).get("models", [])]
        chat_models = [m for m in models if not any(eb in m.lower() for eb in ("bge", "embed", "nomic"))]
        chosen = next((m for m in chat_models if "14b" in m or "8b" in m), chat_models[0] if chat_models else "qwen3:14b")
        body = json.dumps({
            "model": chosen,
            "prompt": prompt,
            "think": False,
            "stream": False,
            "options": {"num_predict": 60, "temperature": 0.2},
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            tip = (json.loads(resp.read().decode("utf-8")).get("response") or "").strip()
            tip = re.sub(r"<think>.*?</think>", "", tip, flags=re.DOTALL).strip()
            if tip:
                return f"({chosen}) {tip}"
    except Exception:
        pass

    # 2. Fallback: Try local LM Studio (Apple MLX / GGUF OpenAI-compatible localhost:1234)
    try:
        lm_body = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 60,
            "temperature": 0.2,
        }).encode("utf-8")
        req2 = urllib.request.Request(
            "http://127.0.0.1:1234/v1/chat/completions",
            data=lm_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=2.5) as resp2:
            d2 = json.loads(resp2.read().decode("utf-8"))
            tip2 = d2["choices"][0]["message"]["content"].strip()
            tip2 = re.sub(r"<think>.*?</think>", "", tip2, flags=re.DOTALL).strip()
            if tip2:
                return f"(Local MLX) {tip2}"
    except Exception:
        pass
    return None


def inject_uploaded_gds_into_session(session: dict, gds_info: dict) -> dict:
    """Update Copilot session with polygon-extracted dimensions from an uploaded `.gds`/`.oas`."""
    ext = gds_info["extracted_geometry"]
    cfg = dict(session["config"])
    for key in (
        "topology",
        "ring_radius_um",
        "ring2_radius_um",
        "ring_width_um",
        "bus_width_um",
        "gap_thru_um",
        "gap_drop_um",
        "inter_ring_gap_um",
        "straight_length_um",
        "pulley_angle_thru_deg",
    ):
        if key in ext and ext[key] is not None:
            cfg[key] = ext[key]

    session["config"] = cfg
    session["stage"] = "gds_uploaded"
    confirmed = set(session.get("confirmed", []))
    confirmed.update(["topology", "resonator_size", "uploaded_gds"])
    session["confirmed"] = sorted(confirmed)

    msg = (
        f"Parsed uploaded layout **`{gds_info['file_name']}`** (cell `{gds_info['cell_name']}`, "
        f"core layer `{gds_info['selected_core_layer'][0]}/{gds_info['selected_core_layer'][1]}`):\n"
        f"- **Detected Topology**: `{ext['topology_display']}` ({ext['ports_detected']}-port)\n"
        f"- **Measured XY Geometry**: `R = {ext['ring_radius_um']:.3f} um`, `W_ring = {ext['ring_width_um']:.3f} um`, "
        f"`W_bus = {ext['bus_width_um']:.3f} um`, `gap_thru = {ext['gap_thru_um']*1000:.1f} nm`"
        + (f", `L_s = {ext['straight_length_um']:.2f} um`" if ext["straight_length_um"] > 0 else "")
        + (f", `theta_pulley = {ext['pulley_angle_thru_deg']:.1f} deg`" if "pulley" in ext["topology"] else "")
        + "\n\n"
        "Because GDSII is a 2D planar mask, please **confirm the vertical wafer stack** "
        "(`Core Material`, `H_film`, `H_slab`, `Cladding`, `Wavelength`) so I can solve the 2D bent eigenmodes and optical spectrum:"
    )
    chips = [
        {"label": "220 nm SOI + Simulate GDS", "prompt": "220 nm SOI strip, SiO2 clad, TE0 at 1550 nm, simulate"},
        {"label": "400 nm Si3N4 + Simulate GDS", "prompt": "400 nm Si3N4 strip, SiO2 clad, TE0 at 1550 nm, simulate"},
        {"label": "600 nm 4H-SiC + Simulate GDS", "prompt": "600 nm 4H-SiC strip, SiO2 clad, TE0 at 1550 nm, simulate"},
        {"label": "600 nm X-cut TFLN (300nm slab) + Simulate", "prompt": "600 nm X-cut TFLN with 300 nm slab, SiO2 clad, TE0 at 1550 nm, simulate"},
    ]
    session["history"] = (session.get("history", []) + [{"role": "assistant", "content": msg}])[-16:]
    return {
        "session": session,
        "assistant_message": msg,
        "chips": chips,
        "active_tab": "tab-gds",
    }


def _solve_radius_for_target_fsr(cfg: MRRDesignConfig, target_fsr_ghz: float | None, target_fsr_nm: float | None, ng_est: float) -> float:
    """Compute ring radius `R` [um] that hits the user's requested FSR given group index `n_g`."""
    wl_m = cfg.wavelength_nm * 1e-9
    if target_fsr_ghz and target_fsr_ghz > 0:
        l_rt_m = C0_M_PER_S / (ng_est * target_fsr_ghz * 1e9)
    elif target_fsr_nm and target_fsr_nm > 0:
        l_rt_m = (wl_m * wl_m) / (ng_est * target_fsr_nm * 1e-9)
    else:
        return cfg.ring_radius_um

    ls_um = cfg.straight_length_um if cfg.topology.startswith("racetrack") else 0.0
    r_um = (l_rt_m * 1e6 - 2.0 * ls_um) / (2.0 * math.pi)
    return round(float(np.clip(r_um, 5.0, 800.0)), 2)


def process_chat_turn(
    session: dict | None,
    user_message: str,
    *,
    gds_export_dir: str | Path,
    use_ollama: bool = False,
) -> dict:
    """Process one user message in the Conversational Photonics Copilot and run live physics."""
    if not session:
        session = create_initial_session()

    intent = parse_photonics_intent(user_message)
    zh = intent["lang"] == "zh"

    if intent["action"] == "reset":
        fresh = create_initial_session()
        return {
            "session": fresh,
            "assistant_message": fresh["history"][-1]["content"],
            "chips": get_welcome_chips(),
            "active_tab": "tab-mrr",
        }

    cfg_dict = dict(session["config"])
    confirmed = set(session.get("confirmed", []))
    history = list(session.get("history", []))
    history.append({"role": "user", "content": user_message})

    # Apply platform preset FIRST if user switched core material (preserving explicit overrides in the same message)
    new_mat = intent["fields"].get("core_material")
    if new_mat and (new_mat != cfg_dict.get("core_material") or "core_material" not in confirmed):
        preset_key = "ScAlN_20" if new_mat.startswith("ScAlN") else new_mat
        if preset_key in PLATFORM_PRESETS and "uploaded_gds" not in confirmed:
            for pk, pv in PLATFORM_PRESETS[preset_key].items():
                if pk != "w_sweep":
                    cfg_dict[pk] = pv
        elif preset_key in PLATFORM_PRESETS and "uploaded_gds" in confirmed:
            # Keep GDS XY layout dimensions, only apply vertical stack defaults!
            for pk in ("film_height_um", "slab_height_um", "sidewall_deg", "clad_material", "top_clad_material", "wavelength_nm"):
                if pk in PLATFORM_PRESETS[preset_key]:
                    cfg_dict[pk] = PLATFORM_PRESETS[preset_key][pk]
        confirmed.add("core_material")

    # Apply parsed fields
    for k, v in intent["fields"].items():
        cfg_dict[k] = v
        if k in ("film_height_um", "slab_height_um", "sidewall_deg", "top_clad_material"):
            confirmed.add("wafer_stack")
        if k == "polarization":
            confirmed.add("polarization")
        if k == "topology":
            confirmed.add("topology")
        if k in ("ring_radius_um", "gap_thru_um", "pulley_angle_thru_deg", "straight_length_um"):
            confirmed.add("resonator_size")
        if k in ("ring_width_um", "bus_width_um"):
            confirmed.add("explicit_widths")

    # Handle port count toggle (`4-port add-drop` vs `2-port all-pass`) without changing coupler type
    if "ports" in intent["targets"] and "topology" not in intent["fields"]:
        want_4 = intent["targets"]["ports"] == 4
        cur_t = cfg_dict["topology"]
        if cur_t.startswith("pulley"):
            cfg_dict["topology"] = "pulley_ad" if want_4 else "pulley_ap"
        elif cur_t.startswith("racetrack"):
            cfg_dict["topology"] = "racetrack_ad" if want_4 else "racetrack_ap"
        elif cur_t != "vernier_crow_ad":
            cfg_dict["topology"] = "point_circular_ad" if want_4 else "point_circular_ap"
        confirmed.add("topology")

    if "fsr_ghz" in intent["targets"]:
        session["target_fsr_ghz"] = intent["targets"]["fsr_ghz"]
        session["target_fsr_nm"] = None
        confirmed.add("resonator_size")
    elif "fsr_nm" in intent["targets"]:
        session["target_fsr_nm"] = intent["targets"]["fsr_nm"]
        session["target_fsr_ghz"] = None
        confirmed.add("resonator_size")

    session["config"] = cfg_dict
    session["confirmed"] = sorted(confirmed)
    cfg = _dict_to_cfg(cfg_dict)

    # ------------------------------------------------------------------
    # Direct Action 1: Apply Critical Coupling (`g_CC` / `theta_CC` / `L_s,CC`)
    # ------------------------------------------------------------------
    if intent["action"] == "apply_critical_coupling":
        last_m = session.get("last_mrr_metrics")
        if not last_m:
            res_init = simulate_mrr_topology(cfg)
            cc = res_init["critical_coupling"]
        else:
            cc = last_m["critical_coupling"]
        p_name = cc["parameter"]
        cfg_dict[p_name] = float(cc["recommended_value"])
        if cfg_dict["topology"].endswith("_ad") and p_name == "gap_thru_um":
            cfg_dict["gap_drop_um"] = round(float(cc["recommended_value"]) + 0.06, 4)
        session["config"] = cfg_dict
        cfg = _dict_to_cfg(cfg_dict)
        mrr_res = simulate_mrr_topology(cfg)
        session["last_mrr_metrics"] = {
            "metrics": mrr_res["metrics"],
            "critical_coupling": mrr_res["critical_coupling"],
        }
        session["stage"] = "mrr_synthesized"
        m = mrr_res["metrics"]
        msg = (
            f"Applied synthesized critical-coupling target **`{p_name} = {cc['recommended_value']} {cc['unit']}`** and re-solved:\n"
            f"- **Loaded / Intrinsic Q**: `Q_L = {m['Q_loaded']:,.0f}` | `Q_int = {m['Q_int']:,.0f}` (`Q_ext = {m['Q_ext_thru']:,.0f}`)\n"
            f"- **Through Extinction Ratio**: **`{m['ER_thru_dB']:.1f} dB`** (`FSR = {m['FSR_GHz']:.2f} GHz` / `{m['FSR_nm']:.3f} nm`)\n\n"
            "Would you like to run a **fabrication tolerance sweep** around this point or **export the `.gds` layout**?"
        )
        chips = [
            {"label": "Sweep Coupler Gap", "prompt": "Sweep gap around current design"},
            {"label": "Export Single .GDS + .LYP", "prompt": "Export single GDS layout"},
            {"label": "Export 5-Ring Sweep Array .GDS", "prompt": "Export 5-ring parameter sweep array GDS"},
            {"label": "Sweep Heater Delta_T (0 to 40 K)", "prompt": "Sweep temperature from 0 to 40 K"},
        ]
        session["history"] = (history + [{"role": "assistant", "content": msg}])[-16:]
        return {
            "session": session,
            "assistant_message": msg,
            "chips": chips,
            "mrr_result": mrr_res,
            "active_tab": "tab-mrr",
        }

    # ------------------------------------------------------------------
    # Direct Action 2: Export Single GDS or 5-Ring Sweep Array GDS
    # ------------------------------------------------------------------
    if intent["action"] in ("export_single_gds", "export_sweep_gds"):
        out_dir = Path(gds_export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if intent["action"] == "export_single_gds":
            fname = f"OpenMRR_{cfg.topology}_{cfg.core_material}_R{int(cfg.ring_radius_um)}um.gds"
            gds_path = export_mrr_gds(cfg, out_dir / fname)
            lyp_path = write_klayout_layer_props(Path(gds_path).with_suffix(".lyp"))
            gds_view = analyze_uploaded_gds(gds_path)
            msg = (
                f"Generated foundry-ready single-device layout & KLayout layer file:\n"
                f"- **GDSII File**: `{Path(gds_path).name}` (`R = {cfg.ring_radius_um} um`, `W_ring = {cfg.ring_width_um} um`, `gap = {cfg.gap_thru_um*1000:.0f} nm`)\n"
                f"- **KLayout Layer Map**: `{Path(lyp_path).name}`\n\n"
                "I have loaded the generated polygons into the **GDS Upload & Mask Creator** tab so you can inspect every layer or download the files directly."
            )
        else:
            p_name = TOPOLOGY_CATALOG[cfg.topology]["coupler_param"]
            center = float(getattr(cfg, p_name))
            if p_name.endswith("_um"):
                vals = [round(max(0.10, center + d), 3) for d in (-0.04, -0.02, 0.0, 0.02, 0.04)]
            else:
                vals = [round(max(2.0, center * f), 2) for f in (0.7, 0.85, 1.0, 1.15, 1.30)]
            fname = f"OpenMRR_SweepArray_{cfg.core_material}_{p_name}.gds"
            gds_path = export_sweep_array_gds(cfg, p_name, vals, out_dir / fname)
            lyp_path = str(Path(gds_path).with_suffix(".lyp"))
            gds_view = analyze_uploaded_gds(gds_path)
            msg = (
                f"Created 5-device MPW parameter-sweep array **`{Path(gds_path).name}`** sweeping `{p_name}` across `{vals}`:\n"
                f"- Includes optical port pins (`65/0`), heater/GSG pads (`10/0`, `11/0`), device labels (`66/0`), and KLayout `{Path(lyp_path).name}`."
            )
        chips = [
            {"label": "Back to MRR Spectrum", "prompt": "Simulate current MRR"},
            {"label": "Sweep Coupler Gap", "prompt": "Sweep gap"},
        ]
        session["history"] = (history + [{"role": "assistant", "content": msg}])[-16:]
        return {
            "session": session,
            "assistant_message": msg,
            "chips": chips,
            "gds_export": {"gds_path": gds_path, "lyp_path": lyp_path, "gds_view": gds_view},
            "active_tab": "tab-gds",
        }

    # ------------------------------------------------------------------
    # Direct Action 3: Waveguide Width Dispersion & Single-Mode Check
    # ------------------------------------------------------------------
    preset_key = "ScAlN_20" if cfg.core_material.startswith("ScAlN") else cfg.core_material
    w_min_def, w_max_def = PLATFORM_PRESETS.get(preset_key, {"w_sweep": (0.45, 1.80)})["w_sweep"]

    should_run_width_sweep = (
        intent["action"] == "sweep_width"
        or (
            "core_material" in confirmed
            and session.get("last_width_sweep") is None
            and "resonator_size" not in confirmed
            and intent["action"] != "simulate_mrr"
            and "uploaded_gds" not in confirmed
        )
    )

    if should_run_width_sweep:
        sw_opts = intent.get("sweep") or {}
        w_min = float(sw_opts.get("w_min_um", w_min_def))
        w_max = float(sw_opts.get("w_max_um", w_max_def))
        w_res = run_waveguide_width_sweep(
            core_material=cfg.core_material,
            clad_material=cfg.clad_material,
            top_clad_material=cfg.top_clad_material,
            h_film_um=cfg.film_height_um,
            h_slab_um=cfg.slab_height_um,
            sidewall_deg=cfg.sidewall_deg,
            wavelength_nm=cfg.wavelength_nm,
            w_min_um=w_min,
            w_max_um=w_max,
            num_points=7,
            polarization=cfg.polarization,
            sc_fraction=cfg.sc_fraction,
        )
        # Also solve 2D mode field at recommended ring width so Tab 3 shows crisp |E| field!
        if "explicit_widths" not in confirmed:
            cfg_dict["bus_width_um"] = w_res["recommended_bus_width_um"]
            cfg_dict["ring_width_um"] = w_res["recommended_ring_width_um"]
            session["config"] = cfg_dict
            cfg = _dict_to_cfg(cfg_dict)

        idx_mid = int(np.argmin(np.abs(np.asarray(w_res["widths_um"]) - cfg.ring_width_um)))
        ng_est = float(w_res["ng_fundamental"][idx_mid])
        neff_est = float(w_res["neff_fundamental"][idx_mid])
        session["last_width_sweep"] = {**w_res, "ng_at_rec": ng_est, "neff_at_rec": neff_est}
        session["stage"] = "mode_confirmed"

        msg = (
            f"Solved 2D full-vector Maxwell eigenmodes across `W = {w_min:.2f} – {w_max:.2f} um` on **`{cfg.core_material}`** "
            f"(`H_film = {cfg.film_height_um*1000:.0f} nm`, `H_slab = {cfg.slab_height_um*1000:.0f} nm`, "
            f"`{cfg.top_clad_material}` top clad, `{cfg.polarization}` @ `{cfg.wavelength_nm:.0f} nm`):\n"
            f"- **Single-Mode Cutoff (`TE1`/`TM1` onset)**: `W_SM,max = {w_res['single_mode_max_width_um']:.3f} um`\n"
            f"- **Recommended Widths**: `W_bus = {cfg.bus_width_um:.3f} um` (single-mode) & `W_ring = {cfg.ring_width_um:.3f} um` (`n_eff = {neff_est:.4f}`, `n_g = {ng_est:.4f}`)\n\n"
            "**Next Step — Resonator & Coupler Specs**: What **target FSR** (e.g. `100 GHz` or `200 GHz`) or **radius `R`**, "
            "and which **topology** (`Point Circular`, `Racetrack`, `Pulley Wrap-Around`, `4-Port Add-Drop`, `Vernier`) would you like?"
        )
        chips = [
            {"label": "FSR 200 GHz · Point All-Pass", "prompt": "FSR 200 GHz, point circular all-pass"},
            {"label": "FSR 100 GHz · Pulley All-Pass", "prompt": "FSR 100 GHz, pulley all-pass"},
            {"label": "FSR 100 GHz · 4-Port Add-Drop", "prompt": "FSR 100 GHz, 4-port add-drop"},
            {"label": "R = 60 um · Racetrack All-Pass", "prompt": "R = 60 um, L_s = 20 um, racetrack all-pass"},
            {"label": "Dual-Ring Vernier Filter", "prompt": "R = 40 um, dual-ring Vernier add-drop"},
        ]
        session["history"] = (history + [{"role": "assistant", "content": msg}])[-16:]
        return {
            "session": session,
            "assistant_message": msg,
            "chips": chips,
            "width_sweep_result": w_res,
            "active_tab": "tab-mode",
        }

    # ------------------------------------------------------------------
    # Direct Action 4: MRR Parameter Sweep (`gap`, `pulley angle`, `L_s`, `R`, `Temp`, `Voltage`)
    # ------------------------------------------------------------------
    if intent["action"] == "sweep_mrr":
        sw = intent["sweep"]
        p_name = sw["param_name"]
        rng = sw.get("range")
        if rng:
            vals = np.linspace(rng[0], rng[1], 7).tolist()
        else:
            cur = float(getattr(cfg, p_name))
            if p_name == "gap_thru_um":
                vals = np.linspace(max(0.10, cur - 0.10), cur + 0.12, 7).tolist()
            elif p_name == "pulley_angle_thru_deg":
                vals = np.linspace(max(3.0, cur * 0.35), min(120.0, max(cur * 1.8, 35.0)), 7).tolist()
            elif p_name == "straight_length_um":
                vals = np.linspace(2.0, max(cur * 2.0, 30.0), 7).tolist()
            elif p_name == "ring_radius_um":
                vals = np.linspace(max(10.0, cur * 0.6), cur * 1.5, 6).tolist()
            elif p_name == "delta_temp_k":
                vals = np.linspace(0.0, 50.0, 6).tolist()
            else:
                vals = np.linspace(-15.0, 15.0, 7).tolist()

        sw_res = run_mrr_parameter_sweep(cfg, p_name, vals)
        best_i = sw_res["best_critical_coupling_index"]
        best_v = sw_res["values"][best_i]
        best_er = sw_res["ER_thru_dB"][best_i]
        best_ql = sw_res["Q_loaded"][best_i]
        msg = (
            f"Completed **{len(vals)}-point `{p_name}` sweep** from `{vals[0]:.3g}` to `{vals[-1]:.3g} {sw_res['unit']}`:\n"
            f"- **Peak Extinction Point**: `{p_name} = {best_v:.4g} {sw_res['unit']}` -> `ER = {best_er:.1f} dB`, `Q_loaded = {best_ql:,.0f}`\n"
            f"- **Resonance Shift Across Sweep**: `{sw_res['resonance_shift_pm'][0]:+.1f} pm` to `{sw_res['resonance_shift_pm'][-1]:+.1f} pm`\n\n"
            "The parameter sweep curves (`ER` & `Q_loaded` vs parameter) are plotted on the right workbench."
        )
        chips = [
            {"label": f"Set {p_name}={best_v:.3g} & Simulate", "prompt": f"Set {p_name.replace('_thru_um','').replace('_thru_deg',' angle')} = {best_v:.4g} {sw_res['unit']} and simulate"},
            {"label": "Export 5-Ring Sweep Array .GDS", "prompt": "Export 5-ring parameter sweep array GDS"},
        ]
        session["history"] = (history + [{"role": "assistant", "content": msg}])[-16:]
        return {
            "session": session,
            "assistant_message": msg,
            "chips": chips,
            "mrr_sweep_result": sw_res,
            "active_tab": "tab-mrr",
        }

    # ------------------------------------------------------------------
    # Stage 0 Fallback: If material still unknown, ask for Material & Stack
    # ------------------------------------------------------------------
    if "core_material" not in confirmed:
        msg = (
            "Let's start with **Step 1 (Wafer Material & Stack)**.\n\n"
            "Which waveguide core material and thickness do you want to use (e.g., `220 nm SOI`, "
            "`400 nm Si3N4`, `600 nm 4H-SiC`, `600 nm X-cut TFLN`, `800 nm AlN / ScAlN`, or `Mid-IR Ge`), "
            "or upload an existing `.gds` layout?"
        )
        session["history"] = (history + [{"role": "assistant", "content": msg}])[-16:]
        return {
            "session": session,
            "assistant_message": msg,
            "chips": get_welcome_chips(),
            "active_tab": "tab-mrr",
        }

    # ------------------------------------------------------------------
    # Stage 3: Full 2D Eigenmode + Spatial CMT + Broadband MRR Synthesis
    # ------------------------------------------------------------------
    if (session.get("target_fsr_ghz") or session.get("target_fsr_nm")) and "ring_radius_um" not in intent["fields"]:
        # Estimate n_g from cached width sweep or quick straight-mode evaluation
        ng_est = (session.get("last_width_sweep") or {}).get("ng_at_rec")
        if not ng_est:
            probe_res = simulate_mrr_topology(replace(cfg, num_spectrum_points=400))
            ng_est = float(probe_res["metrics"]["ng_ring"])
        cfg_dict["ring_radius_um"] = _solve_radius_for_target_fsr(
            cfg, session.get("target_fsr_ghz"), session.get("target_fsr_nm"), ng_est
        )
        # Widen spectrum window automatically so at least ~2.2 FSRs are visible
        fsr_nm_approx = (cfg.wavelength_nm ** 2) * 1e-3 / (2.0 * math.pi * cfg_dict["ring_radius_um"] * ng_est)
        cfg_dict["span_nm"] = round(float(np.clip(2.4 * fsr_nm_approx, 3.0, 45.0)), 2)
        session["config"] = cfg_dict
        cfg = _dict_to_cfg(cfg_dict)
        session["target_fsr_ghz"] = None
        session["target_fsr_nm"] = None

    mrr_res = simulate_mrr_topology(cfg)
    m = mrr_res["metrics"]
    cc = mrr_res["critical_coupling"]
    session["last_mrr_metrics"] = {"metrics": m, "critical_coupling": cc}
    session["stage"] = "mrr_synthesized"

    summary = (
        f"Synthesized **`{TOPOLOGY_CATALOG[cfg.topology]['name']}`** on **`{cfg.core_material}`** "
        f"(`H = {cfg.film_height_um*1000:.0f} nm`, `slab = {cfg.slab_height_um*1000:.0f} nm`, "
        f"`W_ring = {cfg.ring_width_um:.2f} um`, `W_bus = {cfg.bus_width_um:.2f} um`, `R = {cfg.ring_radius_um:.2f} um`, `{cfg.polarization}` @ `{cfg.wavelength_nm:.0f} nm`):\n"
        f"- **Eigenmode Indices**: `n_eff = {m['neff_ring']:.5f}`, `n_g = {m['ng_ring']:.5f}`\n"
        f"- **Free Spectral Range**: **`{m['FSR_GHz']:.2f} GHz`** (`{m['FSR_nm']:.3f} nm`)\n"
        f"- **Quality Factors**: `Q_loaded = {m['Q_loaded']:,.0f}` (`Q_int = {m['Q_int']:,.0f}`, `Q_ext = {m['Q_ext_thru']:,.0f}`)\n"
        f"- **Coupling Regime**: `{cc['regime']}` (`ER = {m['ER_thru_dB']:.1f} dB`, `kappa^2 = {m['kappa_power_thru']:.4f}`)\n"
        f"- **Critical-Coupling Target**: **`{cc['parameter']} = {cc['recommended_value']} {cc['unit']}`**"
    )
    if use_ollama:
        compact_kpi = (
            f"{cfg.topology} {cfg.core_material} H={cfg.film_height_um}um W={cfg.ring_width_um}um "
            f"R={cfg.ring_radius_um}um gap={cfg.gap_thru_um}um FSR={m['FSR_GHz']:.1f}GHz "
            f"Q_L={m['Q_loaded']:.0f} ER={m['ER_thru_dB']:.1f}dB {cc['regime']}"
        )
        tip = _maybe_ollama_commentary(compact_kpi)
        if tip:
            summary += f"\n\n*Local LLM*: {tip}"

    chips = [
        {"label": f"Apply Critical Coupling ({cc['recommended_value']} {cc['unit']})", "prompt": "Apply critical coupling"},
        {"label": "Sweep Coupler Gap", "prompt": "Sweep gap"},
        {"label": "Sweep Pulley Angle" if "pulley" in cfg.topology else "Sweep Waveguide Width", "prompt": "Sweep pulley angle" if "pulley" in cfg.topology else "Sweep width"},
        {"label": "Create Single .GDS + .LYP", "prompt": "Export single GDS layout"},
        {"label": "Create 5-Ring Sweep Array .GDS", "prompt": "Export 5-ring parameter sweep array GDS"},
    ]
    session["history"] = (history + [{"role": "assistant", "content": summary}])[-16:]
    return {
        "session": session,
        "assistant_message": summary,
        "chips": chips,
        "mrr_result": mrr_res,
        "active_tab": "tab-mrr",
    }
