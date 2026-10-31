"""Recipe 03: Post-Fabrication Experimental Spectrum CMT Fitting (Split-Doublet & Multi-FSR).

Extracts intrinsic quality factor `Q_int`, external coupling `Q_ext`, propagation
loss `alpha [dB/cm]`, Rayleigh CW/CCW backscattering splitting `2g/2pi [GHz]`, and
group index `n_g` from noisy transmission spectra via BIC model selection.

Run:
    uv run python examples/03_lab_spectrum_fitting/01_fit_doublet_and_multifsr.py
"""
from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from openmrr import fit_multi_resonance_spectrum, fit_single_resonance_cmt, tmm_broadband_mrr_spectrum
from openmrr.mrr_cmt_fit_predict import cmt_split_doublet_power


def main() -> None:
    rng = np.random.default_rng(42)

    # 1. Synthetic noisy high-Q CW/CCW split-doublet trace
    wl_nm = np.linspace(1550.46, 1550.54, 480)
    tr = cmt_split_doublet_power(
        wl_nm,
        lambda0_nm=1550.500,
        kappa_int_ghz=0.16,
        kappa_ext_ghz=0.13,
        mu_split_ghz=0.28,
        baseline_level=0.98,
        baseline_slope_per_nm=-0.03,
    ) + rng.normal(0.0, 0.003, len(wl_nm))

    summary, _, _ = fit_single_resonance_cmt(wl_nm, tr, model_type="auto", known_regime="undercoupled")
    print("=== 1. Auto-BIC Single-Resonance CMT Fit ===")
    print(f"Selected Model   : {summary.model_type} (R^2 = {summary.r_squared:.5f})")
    print(f"Resonance lambda : {summary.lambda0_nm:.5f} nm")
    print(f"Q_loaded / Q_int : {summary.Q_loaded:,.0f} / {summary.Q_int:,.0f} (Q_ext = {summary.Q_ext:,.0f})")
    print(f"Doublet 2g/2pi   : {2.0 * (summary.mu_split_ghz or 0.0):.3f} GHz")

    # 2. Multi-FSR broadband group-index extraction
    r_um = 45.0
    wl_wide = np.linspace(1542.0, 1558.0, 3500)
    broad = tmm_broadband_mrr_spectrum(
        wl_wide,
        radius_um=r_um,
        neff_at_ref=2.01,
        ng_at_ref=2.142,
        lambda_ref_nm=1550.0,
        dispersion_d2_per_nm2=1.0e-5,
        alpha_loss_db_per_cm=0.35,
        kappa_power_thru=0.03,
    )
    multi = fit_multi_resonance_spectrum(
        wl_wide,
        broad["thru_T"] + rng.normal(0.0, 0.002, len(wl_wide)),
        ring_length_um=2.0 * math.pi * r_um,
        known_regime="undercoupled",
    )
    print("\n=== 2. Broadband Multi-FSR Group-Index Fit ===")
    print(f"Resonances Fitted: {multi['num_resonances']}")
    print(f"Mean FSR         : {multi['mean_fsr_ghz']:.2f} GHz ({multi['mean_fsr_nm']:.3f} nm)")
    print(f"Extracted n_g    : {multi['ng_extracted']:.4f} (True n_g = 2.1420)")


if __name__ == "__main__":
    main()
