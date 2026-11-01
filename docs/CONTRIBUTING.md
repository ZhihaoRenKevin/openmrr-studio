# Contributing & Roadmap

Contributions are very welcome, especially new cleanroom material dispersion models, coupler recipes, experimental spectrum benchmarks, and open foundry PDK layer presets.

## Ground Rules

1. **Permissive Licensing Only (`MIT` / `BSD` / `Apache-2.0`)**:
   Every runtime dependency must use a permissive license so students, academic labs, and startups can package standalone apps freely. Do not add `GPL` runtime imports (`microring.conformal_mesher` uses pure-BSD `scikit-fem` + `scipy.spatial.Delaunay` + `shapely`).
2. **Every Physical Number Needs a Published Literature Source**:
   When adding a refractive-index dispersion formula, thermo-optic coefficient `dn/dT`, Pockels tensor component `r_ij`, or Kerr `n_2` in `src/microring/materials.py`, record the published journal reference, crystal cut/orientation, and valid wavelength window `[lambda_min, lambda_max]`.
3. **Explicit Physical Units Everywhere**:
   Suffix geometric and optical arguments with explicit units (`_um`, `_nm`, `_m`, `_deg`, `_ghz`, `_db_per_cm`, `_k`, `_v`) and verify against `tests/test_microring_all.py`.
4. **GDSII Round-Trip Integrity**:
   Any new resonator topology added to `mrr_topologies.py` must export clean polygons without self-intersections and pass `analyze_uploaded_gds` round-trip extraction in `tests/`.

## Development Workflow

```bash
uv sync --extra dev
python tests/test_microring_all.py
```

---

## Roadmap

| Stage | Capability | Status |
| :--- | :--- | :--- |
| **Foundations** | 24-material catalog (`400 nm` to `14 um`), pure-BSD 2D bent/straight vector FEM & single-mode cutoff | **v3.1+ (Ready)** |
| **Devices & GDSII** | 7 MRR topologies (point, racetrack, concentric pulley, Vernier), bidirectional `.gds` caliper & MPW arrays | **v3.1+ (Ready)** |
| **Lab & Desktop** | Bilingual guided UI, `dB/cm` loss workflow, split-doublet CMT fitter, `.dmg`/`.exe` & Claude/Codex MCP | **v3.2+ (Ready)** |
| **Cleanroom Fab** | Positive PR vs. Negative PR over/under-dose analyzer (`ER >= 15 dB` window) & 5-cell pre-biased `.GDS` | **v3.3+ (Ready)** |
| **Active Tuning & IC** | Native 2D-FEM `TO` (`HEAT`), `EO` (Laplace), `Si PN/PIN` (Soref-Bennett), perturbed eigenmodes & Lumerical INTERCONNECT `.zip` | **v3.4+ (Ready)** |
| **Chip I/O & High-Q** | 2D-FEM Butt/Edge couplers, 2D Full-Wave `FDFD` Grating Couplers (`127 um` FA loopback `.GDS`), instant `Q=10^4-10^8+` & 0.8 ps FDTD cutout | **v3.5 (Ready)** |
| **Upcoming** | Broadband Kerr microcomb integrated dispersion (`D_int`, `D_2`, `D_3`) & Lugiato-Lefever preview | Planned |
| **Upcoming** | 3D Subwavelength Grating (`SWG`) effective-medium metamaterial GC & foundry `cspdk`/`ubcpdk` wrappers | Planned |
