# Cross-Solver Verification & Ansys Lumerical Benchmark Protocol

Scientific credibility requires stating exact physical equations, independent cross-solver agreement, and validity boundaries where full 3D time-domain simulation (`3D FDTD`) remains mandatory before foundry tape-out.

---

## 1. Independent Dual-Engine 2D Bent Maxwell Eigenmode Audit (`532 nm` $\rightarrow$ `4200 nm`)

Reproducible locally with zero commercial licenses via:

```bash
python benchmarks/generate_and_audit_benchmarks.py
```

This benchmark solves the **exact same 2D cylindrical bent waveguide cross-sections** across **five integrated-photonics wavebands** (`Visible 532 nm`, `VNIR 780 nm`, `O-Band 1310 nm`, `C-Band 1550 nm`, and `Mid-IR 4200 nm`) using two mathematically independent Maxwell discretizations:
1. **`OpenMRR Conformal Vector FEM` (`scikit-fem`)**: Unstructured 2nd-order curl-conforming `Nedelec1` transverse + `Lagrange P2` azimuthal finite elements (`ElementTriN2 * ElementTriP2`) on an interface-conforming pure-BSD Delaunay mesh with exact cylindrical coordinate transformation $\rho(x) = 1 + x/R$.
2. **`Structured Yee-Grid FDE` (`tidy3d` local CPU `ModeSolver`)**: Finite-difference frequency-domain eigenmode discretization on a staggered Yee lattice (the same discretization family used by commercial FDE mode solvers).

### Verified Cross-Solver Results (`Darwin-arm64`, Python 3.12)

| Case ID | $\lambda$ (nm) | Platform & Stack | $R$ (µm) | $n_{\mathrm{eff}}$ (Conformal FEM) | $n_{\mathrm{eff}}$ (Yee-Grid FDE) | $|\Delta n_{\mathrm{eff}}|$ | $n_g$ | FSR (nm) | $\kappa^2$ (CMT) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Vis_532nm_Si3N4_Strip` | `532.0` | `180 nm Si3N4 / SiO2` | `25.0` | `1.766850` | `1.768019` | **`1.17e-03`** | `2.2519` | `0.800` | `0.0535` |
| `VNIR_780nm_TiO2_Strip` | `780.0` | `200 nm TiO2 / SiO2` (`86°`) | `30.0` | `1.877503` | `1.877864` | **`3.60e-04`** | `2.6911` | `1.199` | `0.0626` |
| `OBand_1310nm_SOI_220nm` | `1310.0` | `220 nm Si / SiO2` | `15.0` | `2.562140` | `2.562321` | **`1.81e-04`** | `4.3593` | `4.177` | `0.0353` |
| `CBand_1550nm_4HSiC_Pulley` | `1550.0` | `600 nm 4H-SiC / SiO2` (`82°`) | `40.0` | `2.275336` | `2.274984` | **`3.52e-04`** | `2.7978` | `3.417` | `0.0365` |
| `MidIR_4200nm_Ge_CaF2` | `4200.0` | `1.4 µm Ge rib (0.3 µm slab) / CaF2 / Air` | `65.0` | `3.704086` | `3.703304` | **`7.82e-04`** | `4.3295` | `9.168` | `0.0063` |

> **Why Conformal FEM Matters on Slanted High-Index Sidewalls**: On high-contrast slanted sidewalls (`Si` or `Ge` with `82°–88°` etch angles), a coarse Cartesian Yee grid without subpixel permittivity averaging snaps the slanted wall to the nearest Yee cell face, introducing `1e-2` staircase bias unless `dl <= 5–10 nm`. OpenMRR's transfinite conformal triangular mesher aligns element edges directly along angled sidewalls at any angle `70°–90°` with zero staircasing.

---

## 2. Commercial Ansys Lumerical (`MODE FDE` + `3D FDTD`) Validation Runner

On a workstation equipped with Ansys Lumerical (`lumapi`), execute a head-to-head validation of both 2D bent eigenmodes (`MODE FDE`) and 3D bus-to-ring coupler S-parameters (`3D FDTD`, `auto shutoff min = 1e-5`) across point, racetrack, and $C^1$-smooth concentric pulley couplers:

```bash
# Step 1: Export canonical benchmark specifications & .gds masks
python benchmarks/generate_and_audit_benchmarks.py

# Step 2: Run head-to-head Ansys Lumerical MODE FDE + 3D FDTD comparison
python benchmarks/run_lumapi_validation.py
```

This generates `benchmarks/outputs/lumerical_vs_openmrr_validation.csv` and `LUMERICAL_VALIDATION_REPORT.md` with matched diagonal refractive index tensors `(nx, ny, nz)`, sidewall angles, slab heights, and fundamental-mode port expansions (`|S21|^2`).

---

## 3. Native 2D-FEM Active Tuning & Lumerical INTERCONNECT Passivity Verification (`v3.4.0`)

Reproducible locally with zero COMSOL or Lumerical licenses via:

```bash
python examples/01_devices_and_sweeps/05_active_tuning_pn_eo_to_interconnect.py
python tests/test_openmrr_all.py
```

OpenMRR Studio `v3.4.0` solves cross-section active perturbations natively in `scikit-fem` and injects cell-wise $\Delta\varepsilon(x,y) = (n_0 + \Delta n + i\Delta k)^2 - n_0^2$ (`ElementDG(ElementTriP1())`) directly into the 2D curl-conforming `Nedelec1 * Lagrange P2` Maxwell eigenmode solver (`solve_perturbed_neff_sweep_fem`):

| Active Mechanism | Cross-Section PDE / Carrier Physics | Verified Benchmark (`Darwin-arm64`) | Extracted Figure of Merit |
| :--- | :--- | :--- | :--- |
| **`si_pn_depletion`** (`220 nm` Si rib, `90 nm` slab, `0..-5 V`) | Poisson $W_{\mathrm{dep}}(V)$ + Debye-screened 2D carriers + Soref-Bennett $\Delta n + i\Delta k$ | `R = 20 µm`, `1550 nm` | `11.53 pm/V`, $V_\pi L = 2.088\text{ V}\cdot\text{cm}$, $f_{3\mathrm{dB}} = 6.29\text{ GHz}$ |
| **`pockels_eo`** (`600 nm` X-cut TFLN, `GSG` electrodes) | 2D anisotropic Laplace $-\nabla\cdot(\varepsilon_0\boldsymbol{\varepsilon}_{\mathrm{DC}}\nabla\phi)=0$ + tensor $r_{ij}$ | `G = 5.0 -> 3.2 µm` | $V_\pi L = 5.358 \rightarrow 3.603\text{ V}\cdot\text{cm}$, $f_{3\mathrm{dB}} = 19.02\text{ GHz}$ |
| **`thermo_optic`** (`400 nm` Si3N4 + `TiN` microheater) | 2D Fourier heat conduction $-\nabla\cdot(\kappa_{\mathrm{th}}\nabla\Delta T)=Q_{\mathrm{vol}}$ | `BOX = 2.0 -> 3.5 µm` | $R_{\mathrm{th}} = 1.153 \rightarrow 1.566\text{ K/mW}$, $P_\pi = 156.8 \rightarrow 115.5\text{ mW}$ |
| **Lumerical INTERCONNECT (`SPAR .dat`)** | Multi-state complex S-matrix export (`|S21|^2 + |S31|^2 <= 1`) | `1875` frequency pts/state | `passivity = True` across all bias states |

---

## 4. Physical Scope Boundaries

- **High-Confidence Regime (`OpenMRR Studio` 2D Bent FEM + Spatial CMT + 2D Multiphysics FEM)**:
  - Guided straight and moderately bent waveguide dispersion ($n_{\mathrm{eff}}$, $n_g$, FSR, single-mode cutoff $W_{\mathrm{SM}}$);
  - Weak-to-moderate evanescent couplers (`gap >= 150 nm` in NIR, `>= 300 nm` in Mid-IR) including phase-mismatched wrap-around pulley couplers;
  - Cross-sectional 2D Fourier thermo-optic (`TiN`/`Pt`/`W` microheaters), 2D Laplace Pockels electro-optic (`GSG`/vertical electrodes), and Silicon PN depletion / PIN injection perturbed eigenmode shifts;
  - Positive vs. negative photoresist exposure-dose / CD-bias coupling drift and 5-cell pre-biased mask synthesis;
  - Post-fabrication Lorentzian, CW/CCW Split-Doublet, Fano, and Multi-FSR transmission fitting.
- **Regimes Requiring Full `3D FDTD` / `3D TCAD` Before Final Foundry Tape-Out**:
  - Ultra-tight sub-`120 nm` high-index-contrast gaps where strong supermode distortion and parasitic coupler radiation loss ($1 - |S_{21}|^2 - |S_{31}|^2 > 1\%$) occur;
  - Abrupt straight-to-bend racetrack junctions without adiabatic Euler transitions, or 3D in-plane longitudinal heat spreading near short heater corners / thermal isolation trenches;
  - Ultra-sharp bends ($R < 5\,\mu\text{m}$ in `Si3N4` or thin-BOX substrate leakage) where radiative $Q_{\mathrm{rad}}$ limits unloaded $Q_{\mathrm{int}}$.
