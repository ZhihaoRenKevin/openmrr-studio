# Changelog

All notable changes to **OpenMRR Studio** are documented in this file.

## [3.2.0] - 2026-10-31

### Added
- **6-Step Guided Bilingual (`EN | 中文`) Conversational UI (`ui_frontend.py`, `copilot.py`)**:
  - Redesigned the studio into a spacious, zero-overload step-by-step guided chatbot (`1. Goal` → `2. Waveband` → `3. Material` → `4. Stack & 2D Mode` → `5. Propagation Loss & Ring/FSR` → `6. Critical Coupling & GDS`) with a progressive right-hand visual stage and an optional slide-over `⚙ Expert Controls` drawer.
  - Added a top-bar **`EN | 中文`** language switch translating all UI labels, stepper badges, placeholders, plots, and Copilot prompts/chips instantaneously without losing design state.
- **Bidirectional Waveguide Propagation Loss (`dB/cm`) Workflow (`mrr_cmt_fit_predict.py`, `sweeps.py`, `agent_tools.py`)**:
  - Added exact group-index conversions `loss_db_per_cm_to_q_int` and `q_int_to_loss_db_per_cm`, propagation loss sweeps (`alpha_loss_db_per_cm`), and `--loss` CLI/MCP support.
  - Upgraded the Lab Spectrum CMT Fitter to accept both linear-power and logarithmic `dB`/`dBm` `.CSV`/`.TXT` traces, extract propagation loss $\alpha$ (`dB/cm`) + $Q_{\mathrm{int}}$ + self-consistent multi-FSR $n_g$, and hand off extracted loss to new ring critical-coupling synthesis in 1 click.
- **Native Desktop Installers (`.dmg` & `.exe`) + Offline/Online (`Claude` & `Codex`) Modes**:
  - Added `src/openmrr/build_standalone.py`, `packaging/windows_installer.iss`, and `packaging/build_installers_workflow.yml` to compile zero-Python standalone installers (`OpenMRR-Studio-v3.2.0-macOS-AppleSilicon.dmg` and `OpenMRR-Studio-v3.2.0-Windows-Setup-x64.exe`).
  - Added a 4-mode AI Engine switcher in the Studio UI (`⚡ Offline` | `🖥 Local Ollama/MLX` | `🟣 Online · Claude` | `🟢 Online · Codex / OpenAI`), supporting both locally signed-in `claude` / `codex` CLIs (zero API key needed) and optional in-memory API keys, plus `.devcontainer/devcontainer.json` for 1-click browser launch on GitHub Codespaces.

### Changed
- Removed legacy unused `gmsh`/`femwell` branch in `eigenmode_solver.py` so 100% of core code and dependencies are permissive (`MIT` / `BSD-3-Clause` / `Boost-1.0`, zero GPL).

## [3.1.0] - 2026-10-31

### Added
- **Full Visible (`400 nm`) to Mid-IR (`14.0 µm`) Multi-Waveband Engine**:
  - Expanded `MATERIAL_CATALOG` from 18 to **24 clean-room optical materials**, adding `TiO2` (anatase, athermal $dn/dT < 0$), `Ta2O5`, `GaN` (uniaxial wurtzite), `Diamond` (UV–LWIR), `CaF2`, and `MgF2`.
  - Added realistic interband absorption $k(\lambda) > 0$ below bandgap (`Si < 1.12 µm`, `a-Si < 0.85 µm`, `Ge < 1.90 µm`) and Mid-IR multiphonon absorption $k(\lambda) > 0$ for `SiO2` above `3.60 µm`, coupled directly into cavity $Q_{\mathrm{int}}$ and live UI compatibility banners (`check_wavelength_compatibility`).
  - Added `WAVEBAND_PRESETS`, UI Waveband & Bottom Cladding (`BOX/Sub`) selectors, multi-waveband Copilot quick-reply chips, and cookbook script `examples/01_devices_and_sweeps/03_multiband_vis_1310_midir.py`.
- **Cross-Solver & Commercial Lumerical Validation Suite (`benchmarks/lumerical_validation/`)**:
  - Added `generate_and_audit_benchmarks.py` verifying `< 1.2e-3` $|\Delta n_{\mathrm{eff}}|$ agreement (`1.81e-4` on O-band SOI, `3.52e-4` on C-band 4H-SiC, `7.82e-4` on Mid-IR Ge/CaF2) between OpenMRR's BSD Conformal Vector FEM and Yee-grid FDE across `532 nm` to `4200 nm`.
  - Added `run_lumapi_validation.py` for automated head-to-head Ansys Lumerical `MODE FDE` + `3D FDTD` coupler S-parameter validation.
- **AI Agent & MCP Discovery Infrastructure**:
  - Added root `llms.txt`, Model Context Protocol Registry `server.json`, `--clad` / `--top-clad` CLI flags on `openmrr agent design`, and cross-platform GitHub Actions CI (`.github/workflows/ci.yml`).

### Fixed
- Fixed air-clad / asymmetric-cladding dielectric perturbation $\Delta\varepsilon$ in `mrr_topologies.py` to reference the upper cladding surrounding the etched waveguide ridge (`top_clad_material`) rather than the bottom substrate (`clad_material`), and included `L_rt(L_s)` round-trip loss scaling during racetrack critical-coupling root polishing.

## [3.0.0] - 2026-10-31

### Added
- Initial full-stack release of **OpenMRR Studio**:
  - Pure-BSD 2nd-order curl-conforming 2D cylindrical bent/straight Maxwell FEM eigenmode solver (`conformal_mesher.py`, `eigenmode_solver.py`).
  - 7 microring resonator topologies (`point_circular_ap/ad`, `racetrack_ap/ad`, `pulley_ap/ad`, `vernier_crow_ad`) with spatial CMT integration and 1-click critical coupling.
  - Bilingual (`EN` / `中文`) Conversational Photonics Copilot + Retina 2D Web/Desktop UI (`pywebview` + `Starlette`).
  - Bidirectional GDSII / OASIS bridge (`upload .gds -> polygon caliper measurement -> simulate` and `export single/MPW array .gds + KLayout .lyp`).
  - BIC-guided experimental lab spectrum fitter (`Lorentzian`, `Split-Doublet`, `Fano`, `Multi-FSR`).
  - Ultra-low-token (`<150 tokens/call`) MCP stdio server (`openmrr mcp`) and agent CLI (`openmrr agent`) with local SSD mode caching.
