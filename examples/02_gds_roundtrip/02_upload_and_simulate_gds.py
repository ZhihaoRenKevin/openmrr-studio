"""Recipe 02b: Upload / Read Any External `.gds` -> Auto-Extract Geometry -> Simulate Spectrum.

Demonstrates how MicroRing Studio inspects raw GDSII polygons (`gdstk` + `shapely`),
identifies the topology (`Circular` / `Racetrack` / `Pulley` / `Dual-Ring Vernier`),
measures `R`, `W_ring`, `W_bus`, `gap`, `L_s`, and `pulley_angle` without Python object
metadata, and feeds those exact dimensions straight into the 2D FEM + CMT solver.

Run:
    uv run python examples/02_gds_roundtrip/02_upload_and_simulate_gds.py
"""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import MRRDesignConfig, analyze_uploaded_gds, export_mrr_gds, simulate_mrr_topology


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "cookbook_gds"
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_gds = out_dir / "external_racetrack_sample.gds"

    # 1. Create a sample GDS file (simulating a layout received from a colleague or KLayout)
    truth_cfg = MRRDesignConfig(
        topology="racetrack_ad",
        core_material="Si3N4",
        ring_radius_um=38.0,
        ring_width_um=1.15,
        bus_width_um=0.95,
        straight_length_um=16.0,
        gap_thru_um=0.25,
        gap_drop_um=0.30,
    )
    export_mrr_gds(truth_cfg, sample_gds)

    # 2. Inspect ONLY the binary .gds file
    info = analyze_uploaded_gds(sample_gds)
    ext = info["extracted_geometry"]
    print("=== Polygon-Extracted Geometry from GDSII ===")
    for k, v in ext.items():
        print(f"  {k:<24}: {v}")

    # 3. Combine GDS planar geometry with vertical wafer stack & run optical simulation
    sim_cfg = MRRDesignConfig(
        topology=ext["topology"],
        core_material="Si3N4",
        clad_material="SiO2",
        top_clad_material="SiO2",
        film_height_um=0.40,
        slab_height_um=0.0,
        sidewall_deg=85.0,
        ring_radius_um=ext["ring_radius_um"],
        ring_width_um=ext["ring_width_um"],
        bus_width_um=ext["bus_width_um"],
        straight_length_um=ext["straight_length_um"],
        gap_thru_um=ext["gap_thru_um"],
        gap_drop_um=ext["gap_drop_um"],
        wavelength_nm=1550.0,
    )
    sim = simulate_mrr_topology(sim_cfg)
    m = sim["metrics"]
    print("\n=== Simulated Optical Spectrum of Uploaded GDS ===")
    print(f"  FSR = {m['FSR_GHz']:.2f} GHz ({m['FSR_nm']:.3f} nm) | Q_loaded = {m['Q_loaded']:,.0f} | ER = {m['ER_thru_dB']:.1f} dB")


if __name__ == "__main__":
    main()
