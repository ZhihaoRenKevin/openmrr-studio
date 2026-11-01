"""Recipe 02a: Create Single-Device & 5-Ring Parameter-Sweep Array GDSII + KLayout `.lyp`.

Exports foundry-clean GDSII masks to `outputs/cookbook_gds/` along with a KLayout
layer-properties file (`.lyp`) so you can open them immediately in KLayout (`klayout -l ...`).

Run:
    uv run python examples/02_gds_roundtrip/01_create_mrr_and_sweep_array_gds.py
"""
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from microring import (
    MRRDesignConfig,
    export_mrr_gds,
    export_sweep_array_gds,
    write_klayout_layer_props,
)


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "cookbook_gds"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = MRRDesignConfig(
        topology="pulley_ad",
        core_material="Si3N4",
        film_height_um=0.40,
        ring_width_um=1.20,
        bus_width_um=0.95,
        ring_radius_um=45.0,
        gap_thru_um=0.24,
        gap_drop_um=0.28,
        pulley_angle_thru_deg=22.0,
        pulley_angle_drop_deg=18.0,
    )

    single_gds = export_mrr_gds(cfg, out_dir / "sin_pulley_add_drop_single.gds")
    single_lyp = write_klayout_layer_props(out_dir / "sin_pulley_add_drop_single.lyp")

    # 5-device MPW pulley wrap-angle sweep chiplet
    angles_deg = [14.0, 18.0, 22.0, 26.0, 30.0]
    array_gds = export_sweep_array_gds(
        cfg,
        "pulley_angle_thru_deg",
        angles_deg,
        out_dir / "sin_pulley_5x_angle_sweep.gds",
    )

    print("Exported Single MRR GDS :", single_gds)
    print("Exported KLayout .lyp   :", single_lyp)
    print("Exported 5x Sweep GDS   :", array_gds)


if __name__ == "__main__":
    main()
