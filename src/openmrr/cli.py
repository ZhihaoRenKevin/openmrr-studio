"""Command-Line Interface (`openmrr`) for `OpenMRR Studio v3.0`.

Supports human interactive modes AND ultra-low-token AI agent / MCP modes:
  openmrr                       # Launch native desktop UI window (falls back to browser)
  openmrr browser               # Open UI in Chrome / Safari / Edge
  openmrr check                 # Print detected GPU/AMX/CPU engine + 100k-pt benchmark
  openmrr analyze-gds ring.gds  # Extract MRR topology & dimensions from any .gds/.oas
  openmrr chat "400 nm Si3N4 pulley all-pass, FSR 150 GHz"
  openmrr mcp                   # Run stdio MCP server for Claude Code / Codex / Antigravity
  openmrr agent <tool> ...      # Token-minimal (<150 tokens) local-compute CLI for AI agents
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent_tools import (
    agent_design_mrr,
    agent_fit_spectrum,
    agent_inspect_gds,
    agent_status,
    agent_sweep_mrr,
    agent_width_cutoff,
)
from .copilot import create_initial_session, process_chat_turn
from .desktop_app import launch_studio
from .gds_bridge import analyze_uploaded_gds
from .hardware_accel import detect_hardware_profile, run_compute_benchmark
from .mcp_server import run_mcp_stdio


def _print_compact(data: dict) -> None:
    print(json.dumps(data, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="openmrr",
        description="OpenMRR Studio v3.1 — License-Free Multi-Waveband Photonics Eigenmode, CMT, GDSII & AI-Agent MCP Suite",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_app = sub.add_parser("app", help="Launch native desktop UI window")
    p_app.add_argument("--port", type=int, default=None)

    p_web = sub.add_parser("browser", help="Launch UI in default web browser")
    p_web.add_argument("--port", type=int, default=None)

    sub.add_parser("check", help="Inspect hardware accelerator & run 100k-pt TMM benchmark")
    sub.add_parser("mcp", help="Start JSON-RPC 2.0 MCP server on stdin/stdout (for Claude / Codex)")

    p_gds = sub.add_parser("analyze-gds", help="Extract ring/racetrack/pulley dimensions from a .gds/.oas file")
    p_gds.add_argument("gds_file", type=str, help="Path to .gds or .oas layout")

    p_chat = sub.add_parser("chat", help="Run a single conversational design prompt in terminal")
    p_chat.add_argument("prompt", type=str, help="Natural-language design specification")

    # Token-minimal subcommands for Codex / Claude Code / Antigravity
    p_ag = sub.add_parser("agent", help="Ultra-compact JSON tools (<150 tokens) executing 100% locally")
    ag_sub = p_ag.add_subparsers(dest="agent_cmd", required=True)

    ag_sub.add_parser("status", help="Compact local hardware & material/topology keys")

    p_aw = ag_sub.add_parser("width-cutoff", help="Local 2D FEM single-mode width sweep")
    p_aw.add_argument("--mat", default="Si3N4")
    p_aw.add_argument("--h", type=float, default=0.40, dest="h_um")
    p_aw.add_argument("--slab", type=float, default=0.0, dest="slab_um")
    p_aw.add_argument("--wl", type=float, default=1550.0, dest="wl_nm")
    p_aw.add_argument("--pol", default="TE0")
    p_aw.add_argument("--wmin", type=float, default=0.50, dest="w_min_um")
    p_aw.add_argument("--wmax", type=float, default=2.00, dest="w_max_um")
    p_aw.add_argument("--json", type=str, default=None, dest="raw_json")

    p_ad = ag_sub.add_parser("design", help="Local 2D FEM + CMT MRR synthesis (+ optional FSR/CC/GDS)")
    p_ad.add_argument("--top", default="point_circular_ap")
    p_ad.add_argument("--mat", default="Si3N4")
    p_ad.add_argument("--clad", default=None, dest="clad_material")
    p_ad.add_argument("--top-clad", default=None, dest="top_clad_material")
    p_ad.add_argument("--h", type=float, default=None, dest="h_um")
    p_ad.add_argument("--slab", type=float, default=None, dest="slab_um")
    p_ad.add_argument("--w-ring", type=float, default=None, dest="w_ring_um")
    p_ad.add_argument("--w-bus", type=float, default=None, dest="w_bus_um")
    p_ad.add_argument("--r", type=float, default=None, dest="r_um")
    p_ad.add_argument("--gap", type=float, default=None, dest="gap_um")
    p_ad.add_argument("--ls", type=float, default=None, dest="ls_um")
    p_ad.add_argument("--theta", type=float, default=None, dest="theta_deg")
    p_ad.add_argument("--wl", type=float, default=None, dest="wl_nm")
    p_ad.add_argument("--pol", default=None)
    p_ad.add_argument("--loss", type=float, default=None, dest="loss_db_cm", help="Propagation loss [dB/cm]")
    p_ad.add_argument("--fsr", type=float, default=None, dest="target_fsr_ghz")
    p_ad.add_argument("--cc", action="store_true", dest="apply_cc")
    p_ad.add_argument("--gds", action="store_true", dest="export_gds")
    p_ad.add_argument("--json", type=str, default=None, dest="raw_json")

    p_as = ag_sub.add_parser("sweep", help="Local multi-point MRR sweep (cached 2D FEM modes)")
    p_as.add_argument("--param", required=False, default="gap_thru_um", dest="param_name")
    p_as.add_argument("--min", type=float, default=0.16, dest="v_min")
    p_as.add_argument("--max", type=float, default=0.32, dest="v_max")
    p_as.add_argument("--n", type=int, default=7, dest="num_points")
    p_as.add_argument("--top", default="point_circular_ap")
    p_as.add_argument("--mat", default="Si3N4")
    p_as.add_argument("--h", type=float, default=None, dest="h_um")
    p_as.add_argument("--r", type=float, default=None, dest="r_um")
    p_as.add_argument("--array-gds", action="store_true", dest="export_array_gds")
    p_as.add_argument("--json", type=str, default=None, dest="raw_json")

    p_ai = ag_sub.add_parser("inspect-gds", help="Compact GDS polygon geometry extraction")
    p_ai.add_argument("gds_path", type=str)
    p_ai.add_argument("--cell", default=None, dest="cell_name")

    p_af = ag_sub.add_parser("fit", help="Compact local lab spectrum CMT fit")
    p_af.add_argument("csv_path", type=str)
    p_af.add_argument("--model", default="auto", dest="model_type")
    p_af.add_argument("--regime", default=None, dest="known_regime")
    p_af.add_argument("--lrt", type=float, default=250.0, dest="ring_length_um")

    args = parser.parse_args()

    if args.cmd in (None, "app"):
        raise SystemExit(launch_studio(browser_only=False, port=getattr(args, "port", None)))

    if args.cmd == "browser":
        raise SystemExit(launch_studio(browser_only=True, port=args.port))

    if args.cmd == "mcp":
        run_mcp_stdio()
        return

    if args.cmd == "check":
        prof = detect_hardware_profile()
        bench = run_compute_benchmark(100_000)
        print(json.dumps({"hardware": prof.to_dict(), "benchmark_100k_pts": bench}, indent=2))
        return

    if args.cmd == "analyze-gds":
        info = analyze_uploaded_gds(args.gds_file)
        summary = {k: v for k, v in info.items() if k != "viewer_layers"}
        print(json.dumps(summary, indent=2))
        return

    if args.cmd == "chat":
        sess = create_initial_session()
        out = process_chat_turn(sess, args.prompt, gds_export_dir=Path.cwd() / "outputs" / "gds_exports")
        print(out["assistant_message"])
        return

    if args.cmd == "agent":
        if args.agent_cmd == "status":
            _print_compact(agent_status())
            return
        if args.agent_cmd == "inspect-gds":
            _print_compact(agent_inspect_gds({"gds_path": args.gds_path, "cell_name": args.cell_name}))
            return
        if args.agent_cmd == "fit":
            _print_compact(agent_fit_spectrum({
                "csv_path": args.csv_path,
                "model_type": args.model_type,
                "known_regime": args.known_regime,
                "ring_length_um": args.ring_length_um,
            }))
            return
        d = {k: v for k, v in vars(args).items() if k not in ("cmd", "agent_cmd", "raw_json") and v is not None}
        if getattr(args, "raw_json", None):
            d.update(json.loads(args.raw_json))
        if args.agent_cmd == "width-cutoff":
            _print_compact(agent_width_cutoff(d))
        elif args.agent_cmd == "design":
            _print_compact(agent_design_mrr(d))
        elif args.agent_cmd == "sweep":
            _print_compact(agent_sweep_mrr(d))


if __name__ == "__main__":
    main()
