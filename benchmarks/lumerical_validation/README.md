# Cross-Solver & Ansys Lumerical Validation Suite

Before switching a scientific simulation repository to public release, every solver assumption and accuracy boundary must be stated transparently and benchmarked reproducibly.

## 1. Two-Stage Verification Architecture

1. **Stage A — Local Dual-Engine Maxwell Eigenmode Cross-Check (Included & Verified Offline)**:
   ```bash
   python benchmarks/lumerical_validation/generate_and_audit_benchmarks.py
   ```
   Compares two independent open-source 2D full-vector Maxwell formulations across **5 wavebands (`532 nm` Visible, `780 nm` VNIR, `1310 nm` O-Band, `1550 nm` C-Band, and `4200 nm` Mid-IR)**:
   - **Engine 1 (`OpenMRR BSD Conformal FEM`)**: Unstructured 2nd-order curl-conforming `Nedelec1/Lagrange P2` cylindrical finite elements (`scikit-fem`).
   - **Engine 2 (`Tidy3D Local CPU Yee FDE`)**: Structured Yee-grid finite-difference eigenmode solver (same Yee-cell discretization family as commercial FDE solvers).
   - Writes `outputs/openmrr_vs_fde_multiband.csv`, `outputs/LOCAL_CROSSCHECK_REPORT.md`, and canonical `.gds` layouts.

2. **Stage B — Commercial Ansys Lumerical (`MODE FDE` + `3D FDTD`) Head-to-Head Runner**:
   ```bash
   python benchmarks/lumerical_validation/run_lumapi_validation.py
   ```
   Run on a workstation with Ansys Lumerical installed (`lumapi`):
   - Injects the **exact** diagonal refractive index tensors `(nx, ny, nz)`, sidewall angles, bend radii, and domain bounds from `outputs/lumerical_cases.json`.
   - Solves `Lumerical MODE FDE` for bent `n_eff` & `n_g` AND `Lumerical 3D FDTD` (`auto shutoff min = 1e-5`) for bus-to-ring coupler S-parameters (`|S31|^2` vs OpenMRR spatial CMT `kappa^2`).
   - Writes `outputs/lumerical_vs_openmrr_validation.csv` and `outputs/LUMERICAL_VALIDATION_REPORT.md`.

## 2. Explicit Scope Boundaries of 2D Eigenmode + Spatial CMT

- **Where OpenMRR Studio excels (`|Delta n_eff| ~ 1e-4 to 2e-3`)**: Guided straight/bent waveguide `n_eff(lambda)`, group index `n_g`, FSR, single-mode cutoff width, thermo/electro-optic tuning shifts, moderate-to-weak evanescent couplers (`gap >= 150 nm` in NIR, `>= 300 nm` in Mid-IR), and experimental lab spectrum CMT fitting.
- **When to run 3D FDTD before foundry tape-out**: Ultra-tight sub-`130 nm` high-contrast couplers (strong supermode distortion / radiation loss), abrupt straight-to-bend racetrack junctions without Euler transitions, and substrate-leakage-limited thin-BOX rings.
