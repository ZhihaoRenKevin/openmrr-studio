# OpenMRR Studio Roadmap

OpenMRR Studio grows in four curriculum levels so students and photonics engineers can move from waveguide fundamentals to multi-ring tape-outs and post-fabrication characterization without commercial solver licenses.

| Level | Module / Recipe | Physics & Layout Chain | Status |
| :--- | :--- | :--- | :--- |
| **0 · Foundations** | Environment, GPU/AMX/CPU auto-probe & 24-material dispersion (`400 nm`–`14 um`) | Literature Sellmeier + `dn/dT` + Pockels `r_ij` + bandgap/multiphonon `k` | **v3.1 (Ready)** |
| | 2D full-vector waveguide dispersion & single-mode cutoff sweep | Pure-BSD conformal `Nedelec1/Lagrange` FEM -> `n_eff(W), n_g(W)` | **v3.1 (Ready)** |
| **1 · Devices & Sweeps** | Point-coupled circular & straight-coupler racetrack MRRs (2- & 4-port) | Cylindrical bent FEM + spatial CMT + X-cut TFLN orientation averaging | **v3.1 (Ready)** |
| | Concentric wrap-around pulley MRRs & 1-click critical coupling | Phase-mismatch `Delta_beta` spatial integration -> exact `theta_CC` | **v3.1 (Ready)** |
| | Dual-ring Vernier & 2nd-order CROW add-drop filters | Inter-ring supermode / transfer-matrix synthesis | **v3.1 (Ready)** |
| | Multi-waveband Visible (`532/780 nm`), O-Band (`1310 nm`), SWIR & Mid-IR (`4.2/7.5 um`) | Wavelength-scaled FEM mesh/boxes + `Ge/CaF2` & `TiO2` synthesis | **v3.1 (Ready)** |
| **2 · Bidirectional GDSII** | Create single-device & MPW parameter-sweep array `.gds` + KLayout `.lyp` | `gdstk` role-mapped core, slab, TiN heater, GSG pads & port pins | **v3.1 (Ready)** |
| | Upload any `.gds` / `.oas` -> auto-extract topology & simulate spectrum | `gdstk` + `shapely` annular/bus caliper extraction -> FEM + CMT | **v3.1 (Ready)** |
| **3 · Lab & Agent Suite** | Experimental spectrum CMT fitter (`Lorentzian`, `Split-Doublet`, `Fano`, `Multi-FSR`) | BIC model selection -> `Q_int`, `Q_ext`, `alpha`, `2g/2pi`, `n_g` | **v3.1 (Ready)** |
| | Token-minimal `<150 tokens/call` MCP server & CLI (`Codex` / `Claude` / `Ollama`) | Local SSD mode cache + scalar JSON KPIs + `.csv`/`.gds` file output | **v3.1 (Ready)** |
| **4 · Upcoming (v3.2+)** | Coupled 2D steady-state electro-thermal (`HEAT`) cross-section solver | `scikit-fem` Poisson/heat -> modal `Delta_T` overlap integral | Planned |
| | Multi-wavelength dispersion-engineered Kerr microcomb (`D_int`) designer | Broadband `D_2 / D_3` integrated dispersion + Lugiato-Lefever preview | Planned |
| | Direct `gdsfactory` / `cspdk` / `ubcpdk` active PDK cell wrappers | Grating-coupler & edge-coupler routed test-frame automation | Planned |
