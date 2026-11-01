"""Recipe 00b: Waveguide Width Dispersion & Exact Single-Mode Cutoff Sweep.

Sweeps bottom waveguide width `W` from 0.60 um to 2.00 um on a 400 nm LPCVD Si3N4
strip stack (SiO2 clad, 85 deg sidewall, TE0 @ 1550 nm) using the pure-BSD 2D
conformal finite-element Maxwell solver (`scikit-fem`).

Run:
    uv run python examples/00_getting_started/01_waveguide_dispersion_sweep.py
"""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import run_waveguide_width_sweep

# ---------------- Top-Level Physical & Geometric Parameters ----------------
CORE_MATERIAL = "Si3N4"       # LPCVD Silicon Nitride
CLAD_MATERIAL = "SiO2"        # Thermal/PECVD SiO2
H_FILM_UM = 0.40              # unit: um
H_SLAB_UM = 0.00              # unit: um (0 = full-etch strip)
SIDEWALL_DEG = 85.0           # unit: deg
WAVELENGTH_NM = 1550.0        # unit: nm
W_MIN_UM = 0.60               # unit: um
W_MAX_UM = 2.00               # unit: um
NUM_POINTS = 8
# ---------------------------------------------------------------------------


def main() -> None:
    res = run_waveguide_width_sweep(
        core_material=CORE_MATERIAL,
        clad_material=CLAD_MATERIAL,
        top_clad_material=CLAD_MATERIAL,
        h_film_um=H_FILM_UM,
        h_slab_um=H_SLAB_UM,
        sidewall_deg=SIDEWALL_DEG,
        wavelength_nm=WAVELENGTH_NM,
        w_min_um=W_MIN_UM,
        w_max_um=W_MAX_UM,
        num_points=NUM_POINTS,
        polarization="TE0",
    )

    print(f"=== {CORE_MATERIAL} ({H_FILM_UM*1000:.0f} nm) TE0 Dispersion & Single-Mode Cutoff ===")
    print(f"{'W [um]':<10} {'n_eff(TE0)':<13} {'n_g(TE0)':<12} {'n_eff(TE1)':<13} {'Regime'}")
    for w, n0, ng, n1, sm in zip(
        res["widths_um"],
        res["neff_fundamental"],
        res["ng_fundamental"],
        res["neff_higher_order"],
        res["is_single_mode"],
    ):
        n1_str = f"{n1:.5f}" if n1 is not None else "---"
        tag = "Single-Mode" if sm else "Multimode (TE1 guided)"
        print(f"{w:<10.3f} {n0:<13.5f} {ng:<12.5f} {n1_str:<13} {tag}")

    print("-" * 68)
    print(f"Single-mode max width : {res['single_mode_max_width_um']:.3f} um")
    print(f"Recommended W_bus     : {res['recommended_bus_width_um']:.3f} um")
    print(f"Recommended W_ring    : {res['recommended_ring_width_um']:.3f} um")


if __name__ == "__main__":
    main()
