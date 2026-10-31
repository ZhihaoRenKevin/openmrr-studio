# Contributing to OpenMRR Studio

Contributions are very welcome — especially new clean-room material dispersion models, coupler recipes, experimental spectrum benchmarks, and open foundry PDK layer presets!

## Ground Rules

1. **Permissive Licensing Only (`MIT` / `BSD` / `Apache-2.0`)**:
   Every runtime dependency must use a permissive license so students, academic labs, and startups can package standalone apps freely. Do not add `GPL` runtime imports (for example, `gmsh` is optional and never imported by default; `openmrr.conformal_mesher` uses pure-BSD `scikit-fem` + `scipy.spatial.Delaunay` + `shapely`).
2. **Every Physical Number Needs a Published Literature Source**:
   When adding a refractive-index dispersion formula, thermo-optic coefficient `dn/dT`, Pockels tensor component `r_ij`, or Kerr `n_2` in `src/openmrr/materials.py`, record the published journal reference, crystal cut/orientation, and valid wavelength window `[lambda_min, lambda_max]`.
3. **Explicit Physical Units Everywhere**:
   Suffix geometric and optical arguments with explicit units (`_um`, `_nm`, `_m`, `_deg`, `_ghz`, `_db_per_cm`, `_k`, `_v`) and verify against `pytest`.
4. **GDSII Round-Trip Integrity**:
   Any new resonator topology added to `mrr_topologies.py` must export clean polygons without self-intersections and pass `analyze_uploaded_gds` round-trip extraction in `tests/`.

## Development Workflow

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```
