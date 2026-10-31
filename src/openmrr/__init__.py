"""OpenMRR Studio (`openmrr`) — License-Free Photonics Eigenmode, CMT & GDSII Suite."""
from __future__ import annotations

__version__ = "3.2.0"

from .agent_tools import (
    agent_design_mrr,
    agent_fit_spectrum,
    agent_inspect_gds,
    agent_status,
    agent_sweep_mrr,
    agent_width_cutoff,
)
from .conformal_mesher import build_conformal_waveguide_mesh
from .copilot import (
    create_initial_session,
    parse_photonics_intent,
    process_chat_turn,
    scale_preset_for_wavelength,
)
from .eigenmode_solver import (
    EigenmodeResult,
    WaveguideCrossSectionSpec,
    solve_modes_fde_tidy3d,
    solve_modes_fem,
)
from .gds_bridge import (
    OPENMRR_LAYERS,
    analyze_uploaded_gds,
    export_sweep_array_gds,
    write_klayout_layer_props,
)
from .hardware_accel import detect_hardware_profile, run_compute_benchmark
from .materials import (
    MATERIAL_CATALOG,
    T_REF_K,
    WAVEBAND_PRESETS,
    check_wavelength_compatibility,
    evaluate_material_dispersion_table,
    get_material_fn,
)
from .mrr_cmt_fit_predict import (
    CMTFitSummary,
    fit_multi_resonance_spectrum,
    fit_single_resonance_cmt,
    loss_db_per_cm_to_q_int,
    q_int_to_loss_db_per_cm,
    tmm_broadband_mrr_spectrum,
)
from .mrr_topologies import (
    MRRDesignConfig,
    TOPOLOGY_CATALOG,
    export_mrr_gds,
    simulate_mrr_topology,
)
from .sweeps import run_mrr_parameter_sweep, run_waveguide_width_sweep

__all__ = [
    "__version__",
    "MATERIAL_CATALOG",
    "OPENMRR_LAYERS",
    "TOPOLOGY_CATALOG",
    "T_REF_K",
    "WAVEBAND_PRESETS",
    "CMTFitSummary",
    "EigenmodeResult",
    "MRRDesignConfig",
    "WaveguideCrossSectionSpec",
    "agent_design_mrr",
    "agent_fit_spectrum",
    "agent_inspect_gds",
    "agent_status",
    "agent_sweep_mrr",
    "agent_width_cutoff",
    "analyze_uploaded_gds",
    "build_conformal_waveguide_mesh",
    "check_wavelength_compatibility",
    "create_initial_session",
    "detect_hardware_profile",
    "evaluate_material_dispersion_table",
    "export_mrr_gds",
    "export_sweep_array_gds",
    "fit_multi_resonance_spectrum",
    "fit_single_resonance_cmt",
    "get_material_fn",
    "loss_db_per_cm_to_q_int",
    "parse_photonics_intent",
    "process_chat_turn",
    "q_int_to_loss_db_per_cm",
    "run_compute_benchmark",
    "run_mrr_parameter_sweep",
    "run_waveguide_width_sweep",
    "scale_preset_for_wavelength",
    "simulate_mrr_topology",
    "solve_modes_fde_tidy3d",
    "solve_modes_fem",
    "tmm_broadband_mrr_spectrum",
    "write_klayout_layer_props",
]
