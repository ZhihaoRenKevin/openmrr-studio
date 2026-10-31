# AGENTS.md — Token-Minimal Local-Compute Protocol for AI Agents

When helping users design, sweep, fit, or lay out photonic microring resonators (MRRs) in this repository, **strictly minimize LLM token usage** and **offload 100% of numerical work to local CPU / Apple Silicon AMX / NVIDIA CUDA compute**.

## Golden Token-Saving Rules
1. **Do NOT read `src/openmrr/*.py` source files** unless the user explicitly asks to modify solver internals.
2. **Do NOT print or inspect raw spectrum/polygon arrays** in stdout. All `openmrr agent` commands automatically save full `.csv` / `.gds` / `.lyp` artifacts under `outputs/agent_runs/` and return **<150 tokens of single-line scalar JSON** (plus persistent local SSD eigenmode caching in `outputs/.mode_cache/`).
3. Prefer MCP tools (`openmrr_*` if configured via `.mcp.json`) or the single-command `openmrr agent` CLI below (`uv run openmrr agent ...` or `PYTHONPATH=src python -m openmrr.cli agent ...`).

## One-Command Local-Compute CLI (`<150 tokens` stdout)

| Task | Command |
| :--- | :--- |
| **Probe GPU/AMX/CPU & valid keys** | `uv run openmrr agent status` |
| **2D FEM single-mode width cutoff** | `uv run openmrr agent width-cutoff --mat Si3N4 --h 0.40 --wl 1550 --pol TE0 --wmin 0.6 --wmax 2.0` |
| **Synthesize MRR + Critical Couple + GDS** | `uv run openmrr agent design --top pulley_ap --mat 4H-SiC --h 0.60 --w-ring 1.10 --w-bus 0.82 --fsr 150 --gap 0.24 --cc --gds` |
| **Multi-point parameter sweep (+ MPW GDS)** | `uv run openmrr agent sweep --top pulley_ap --mat 4H-SiC --param pulley_angle_thru_deg --min 6 --max 24 --n 7 --array-gds` |
| **Extract geometry from `.gds` / `.oas`** | `uv run openmrr agent inspect-gds path/to/layout.gds` |
| **Fit lab spectrum CSV (`Q_int`, doublet)** | `uv run openmrr agent fit path/to/trace.csv --model auto --regime under` |

## Valid Keys Quick Reference
- **7 Topologies (`--top`)**: `point_circular_ap`, `point_circular_ad`, `racetrack_ap`, `racetrack_ad`, `pulley_ap`, `pulley_ad`, `vernier_crow_ad`
- **18 Materials (`--mat`)**: `Si`, `a-Si`, `Si3N4`, `SiRich_SiNx`, `4H-SiC`, `3C-SiC`, `AlN`, `ScAlN_10`, `ScAlN_20`, `ScAlN_30`, `LN_Zcut`, `LN_Xcut`, `Ge`, `Al2O3`, `SiO2`, `GSST_amorphous`, `GSST_crystalline`, `Air`
