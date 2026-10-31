"""Comprehensive Automated Test Suite for OpenMRR Studio v3.0.

Can be executed either with `pytest` (`uv run pytest`) or directly as a standalone
verification script (`python tests/test_openmrr_all.py`).
"""
from __future__ import annotations

import asyncio
import base64
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from openmrr import (
    MATERIAL_CATALOG,
    MRRDesignConfig,
    T_REF_K,
    WaveguideCrossSectionSpec,
    agent_design_mrr,
    agent_fit_spectrum,
    agent_inspect_gds,
    agent_status,
    agent_sweep_mrr,
    analyze_uploaded_gds,
    create_initial_session,
    detect_hardware_profile,
    export_mrr_gds,
    export_sweep_array_gds,
    fit_single_resonance_cmt,
    get_material_fn,
    loss_db_per_cm_to_q_int,
    process_chat_turn,
    q_int_to_loss_db_per_cm,
    run_compute_benchmark,
    run_mrr_parameter_sweep,
    run_waveguide_width_sweep,
    simulate_mrr_topology,
    solve_modes_fem,
)
import openmrr.app_server as srv
from openmrr.mcp_server import handle_mcp_request
from openmrr.mrr_cmt_fit_predict import cmt_split_doublet_power


async def _asgi_request(
    method: str,
    path: str,
    query_string: str = "",
    json_body: dict | None = None,
) -> tuple[int, bytes]:
    """Zero-dependency in-process ASGI caller for testing `openmrr.app_server.app`."""
    raw_body = json.dumps(json_body).encode("utf-8") if json_body is not None else b""
    headers = [(b"host", b"127.0.0.1:8765")]
    if json_body is not None:
        headers.append((b"content-type", b"application/json"))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query_string.encode("ascii"),
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8765),
    }
    sent = False
    status_code = 500
    chunks: list[bytes] = []

    async def receive() -> dict:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": raw_body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        nonlocal status_code
        if message["type"] == "http.response.start":
            status_code = int(message["status"])
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    await srv.app(scope, receive, send)
    return status_code, b"".join(chunks)


def test_materials_and_hardware() -> None:
    assert len(MATERIAL_CATALOG) == 24
    for _key, meta in MATERIAL_CATALOG.items():
        wl_m = float(meta["default_band_nm"]) * 1e-9
        props = meta["fn"](wl_m, T_REF_K)
        assert props.nx >= 1.0
        assert props.ny >= 1.0

    prof = detect_hardware_profile()
    bench = run_compute_benchmark(20_000)
    assert prof.to_dict()["cpu_cores"] >= 1
    assert bench["throughput_mpts_per_s"] > 0.5


def test_pure_bsd_fem_no_gpl() -> None:
    spec = WaveguideCrossSectionSpec(
        w_bottom_um=1.10,
        h_film_um=0.60,
        h_slab_um=0.0,
        sidewall_deg=82.0,
        core_material_fn=get_material_fn("4H-SiC"),
        clad_material_fn=get_material_fn("SiO2"),
        top_clad_material_fn=get_material_fn("SiO2"),
    )
    modes = solve_modes_fem(spec, 1550e-9, bend_radius_m=40e-6, num_modes=2, core_mesh_res_um=0.045)
    assert "gmsh" not in sys.modules
    assert 2.10 < float(np.real(modes[0].n_eff)) < 2.55
    assert modes[0].te_fraction > 0.85


def test_width_and_mrr_sweeps() -> None:
    w_sw = run_waveguide_width_sweep(
        core_material="Si3N4",
        h_film_um=0.40,
        w_min_um=0.70,
        w_max_um=1.80,
        num_points=4,
    )
    assert len(w_sw["widths_um"]) == 4
    assert 0.70 <= w_sw["single_mode_max_width_um"] <= 1.80

    base = MRRDesignConfig(
        topology="pulley_ap",
        core_material="4H-SiC",
        film_height_um=0.60,
        ring_width_um=1.10,
        bus_width_um=0.82,
        ring_radius_um=40.0,
        gap_thru_um=0.25,
    )
    init = simulate_mrr_topology(base)
    theta_cc = float(init["critical_coupling"]["recommended_value"])
    cc_res = simulate_mrr_topology(replace(base, pulley_angle_thru_deg=theta_cc))
    assert cc_res["metrics"]["ER_thru_dB"] > 35.0

    m_sw = run_mrr_parameter_sweep(base, "gap_thru_um", [0.20, 0.25, 0.30])
    assert len(m_sw["ER_thru_dB"]) == 3


def test_bidirectional_gds_roundtrip() -> None:
    cases = [
        ("point_circular_ap", {}),
        ("racetrack_ad", {"straight_length_um": 14.0}),
        ("pulley_ap", {"pulley_angle_thru_deg": 24.0}),
        ("vernier_crow_ad", {"ring2_radius_um": 43.0, "inter_ring_gap_um": 0.35}),
    ]
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        for topology, extra in cases:
            cfg = MRRDesignConfig(
                topology=topology,
                core_material="Si3N4",
                ring_radius_um=40.0,
                ring_width_um=1.20,
                bus_width_um=0.95,
                gap_thru_um=0.25,
                gap_drop_um=0.28,
                **extra,
            )
            gds_file = tmp_path / f"sample_{topology}.gds"
            export_mrr_gds(cfg, gds_file)
            info = analyze_uploaded_gds(gds_file)
            ext = info["extracted_geometry"]

            assert ext["topology"] == topology, f"Expected {topology}, got {ext['topology']}"
            assert abs(ext["ring_radius_um"] - 40.0) < 0.08
            assert abs(ext["ring_width_um"] - 1.20) < 0.04
            assert abs(ext["gap_thru_um"] - 0.25) < 0.02
            if topology == "racetrack_ad":
                assert abs(ext["straight_length_um"] - 14.0) < 0.15

        arr_file = tmp_path / "sweep_arr.gds"
        export_sweep_array_gds(cfg, "gap_thru_um", [0.20, 0.25, 0.30], arr_file)
        assert arr_file.is_file()
        assert arr_file.with_suffix(".lyp").is_file()


def test_conversational_copilot_flow() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        # 1. Guided step-by-step wizard (1 question at a time + dB/cm propagation loss)
        s0 = create_initial_session(lang="en")
        g1 = process_chat_turn(s0, "Start step-by-step microring design", gds_export_dir=tmp_path)
        assert g1["wizard_step"] == 2
        g2 = process_chat_turn(g1["session"], "Wavelength = 1550 nm", gds_export_dir=tmp_path)
        assert g2["wizard_step"] == 3
        g3 = process_chat_turn(g2["session"], "Core material: Si3N4", gds_export_dir=tmp_path)
        assert g3["wizard_step"] == 4
        g4 = process_chat_turn(g3["session"], "Confirm stack and solve 2D modes", gds_export_dir=tmp_path)
        assert "width_sweep_result" in g4 and g4["wizard_step"] == 5
        g5 = process_chat_turn(g4["session"], "Propagation loss = 0.85 dB/cm", gds_export_dir=tmp_path)
        assert g5["wizard_step"] == 5 and abs(g5["session"]["config"]["alpha_loss_db_per_cm"] - 0.85) < 1e-4

        # Live EN -> ZH language switch mid-step without losing design state
        g_lang = process_chat_turn(g5["session"], "__switch_lang__", gds_export_dir=tmp_path, lang="zh")
        assert g_lang["session"]["lang"] == "zh"
        assert abs(g_lang["session"]["config"]["alpha_loss_db_per_cm"] - 0.85) < 1e-4

        g6 = process_chat_turn(g_lang["session"], "FSR 200 GHz, 点耦合两端口", gds_export_dir=tmp_path, lang="zh")
        assert "mrr_result" in g6 and g6["wizard_step"] == 6
        assert abs(g6["mrr_result"]["metrics"]["alpha_loss_db_per_cm"] - 0.85) < 1e-3
        fsr_hit = g6["mrr_result"]["metrics"]["FSR_GHz"]
        assert 180.0 <= fsr_hit <= 220.0

        r3 = process_chat_turn(g6["session"], "Apply critical coupling", gds_export_dir=tmp_path, lang="en")
        assert r3["mrr_result"]["metrics"]["ER_thru_dB"] > 30.0

        r_sw_loss = process_chat_turn(r3["session"], "Sweep propagation loss", gds_export_dir=tmp_path, lang="en")
        assert "mrr_sweep_result" in r_sw_loss
        assert r_sw_loss["mrr_sweep_result"]["param_name"] == "alpha_loss_db_per_cm"

        r4 = process_chat_turn(r3["session"], "Export single GDS layout", gds_export_dir=tmp_path)
        assert "gds_export" in r4
        assert Path(r4["gds_export"]["gds_path"]).is_file()

        # 2. Fast-forward Chinese one-shot prompt
        r_zh = process_chat_turn(
            create_initial_session(lang="zh"),
            "220 nm SOI 跑道微环 四端口 损耗 1.8 dB/cm FSR 150 GHz 开始仿真",
            gds_export_dir=tmp_path,
            lang="zh",
        )
        assert r_zh["session"]["config"]["core_material"] == "Si"
        assert r_zh["session"]["config"]["topology"] == "racetrack_ad"
        assert abs(r_zh["mrr_result"]["metrics"]["alpha_loss_db_per_cm"] - 1.8) < 1e-3


def test_cmt_spectrum_fitter() -> None:
    # Exact bidirectional loss [dB/cm] <-> Q_int identity check
    q_calc = loss_db_per_cm_to_q_int(0.75, ng=2.12, wavelength_nm=1550.0)
    alpha_back = q_int_to_loss_db_per_cm(q_calc, ng=2.12, wavelength_nm=1550.0)
    assert abs(alpha_back - 0.75) < 1e-6

    wl = np.linspace(1550.47, 1550.53, 300)
    tr = cmt_split_doublet_power(
        wl, 1550.500, kappa_int_ghz=0.18, kappa_ext_ghz=0.14, mu_split_ghz=0.26
    )
    summary, _, _ = fit_single_resonance_cmt(
        wl, tr, model_type="auto", known_regime="undercoupled", ng_assumed=2.10, ring_length_um=250.0
    )
    assert summary.model_type == "split_doublet"
    assert summary.r_squared > 0.999
    assert summary.alpha_loss_db_per_cm > 0.05

    # Also test logarithmic dB/dBm trace auto-conversion
    tr_dbm = -8.5 + 10.0 * np.log10(np.clip(tr, 1e-5, None))
    summary_db, _, _ = fit_single_resonance_cmt(
        wl, tr_dbm, model_type="split_doublet", known_regime="undercoupled", ng_assumed=2.10
    )
    assert abs(summary_db.alpha_loss_db_per_cm - summary.alpha_loss_db_per_cm) < 0.03


def test_http_endpoints_and_gds_upload() -> None:
    async def _run() -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            old_exp, old_up = srv.GDS_EXPORT_DIR, srv.GDS_UPLOAD_DIR
            srv.GDS_EXPORT_DIR = tmp_path / "exports"
            srv.GDS_UPLOAD_DIR = tmp_path / "uploads"
            try:
                st, body = await _asgi_request("GET", "/")
                assert st == 200 and b"OpenMRR Studio" in body and b"setLanguage('zh')" in body

                st, body = await _asgi_request("GET", "/api/materials")
                assert st == 200 and len(json.loads(body)["materials"]) == 24

                st, body_zh = await _asgi_request("POST", "/api/chat_init", query_string="lang=zh")
                assert st == 200 and json.loads(body_zh)["session"]["lang"] == "zh"

                st, body = await _asgi_request("POST", "/api/chat_init")
                init = json.loads(body)

                st, body = await _asgi_request("GET", "/api/ai_backends")
                assert st == 200
                ai_bk = json.loads(body)
                assert ai_bk["offline"] is True and "claude_cli_available" in ai_bk and "codex_cli_available" in ai_bk

                st, body = await _asgi_request(
                    "POST",
                    "/api/chat",
                    json_body={
                        "session": init["session"],
                        "message": "220 nm SOI strip, TE0 at 1550 nm, R = 15 um, simulate",
                        "ai_mode": "offline",
                    },
                )
                assert st == 200
                chat = json.loads(body)
                assert "mrr_result" in chat and chat.get("ai_mode") == "offline"

                st, body = await _asgi_request("POST", "/api/export_gds", json_body=chat["session"]["config"])
                assert st == 200
                exp = json.loads(body)

                q_str = exp["gds_download_url"].split("?", 1)[1]
                st, gds_bytes = await _asgi_request("GET", "/api/download_file", query_string=q_str)
                assert st == 200 and len(gds_bytes) > 100

                b64_gds = base64.b64encode(gds_bytes).decode("ascii")
                st, body = await _asgi_request(
                    "POST",
                    "/api/upload_gds",
                    json_body={"filename": "roundtrip_test.gds", "content_b64": b64_gds, "session": chat["session"]},
                )
                assert st == 200
                up = json.loads(body)
                assert abs(up["gds_info"]["extracted_geometry"]["ring_radius_um"] - 15.0) < 0.08
            finally:
                srv.GDS_EXPORT_DIR, srv.GDS_UPLOAD_DIR = old_exp, old_up

    asyncio.run(_run())


def test_agent_tools_and_mcp_minimal_tokens() -> None:
    # 1. MCP handshake + tools/list
    init_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp is not None and init_resp["result"]["serverInfo"]["name"] == "openmrr-studio"
    list_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert list_resp is not None and len(list_resp["result"]["tools"]) == 6

    # 2. Compact MCP design + critical coupling + GDS export (< 550 chars => < ~140 tokens!)
    call_resp = handle_mcp_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "openmrr_design_mrr",
            "arguments": {
                "top": "pulley_ap",
                "mat": "4H-SiC",
                "h_um": 0.60,
                "w_ring_um": 1.10,
                "w_bus_um": 0.82,
                "r_um": 40.0,
                "gap_um": 0.25,
                "apply_cc": True,
                "export_gds": True,
            },
        },
    })
    assert call_resp is not None and not call_resp["result"]["isError"]
    compact_text = call_resp["result"]["content"][0]["text"]
    assert len(compact_text) < 600, f"Agent response too verbose ({len(compact_text)} chars): {compact_text}"
    parsed = json.loads(compact_text)
    assert parsed["ER_dB"] > 35.0
    assert Path(parsed["gds"]).is_file()

    # 3. Inspect exported GDS & run cached sweep (< 600 chars each)
    gds_kpi = agent_inspect_gds({"gds_path": parsed["gds"]})
    assert gds_kpi["extracted"]["topology"] == "pulley_ap"
    sw_kpi = agent_sweep_mrr({
        "top": "pulley_ap",
        "mat": "4H-SiC",
        "h_um": 0.60,
        "w_ring_um": 1.10,
        "w_bus_um": 0.82,
        "r_um": 40.0,
        "gap_um": 0.25,
        "param_name": "gap_thru_um",
        "v_min": 0.20,
        "v_max": 0.30,
        "num_points": 5,
    })
    assert len(json.dumps(sw_kpi, separators=(",", ":"))) < 450


def test_multiband_vis_1310_midir_and_warnings() -> None:
    # 1. Visible 532 nm Si3N4
    vis = simulate_mrr_topology(
        MRRDesignConfig(
            topology="point_circular_ap",
            core_material="Si3N4",
            clad_material="SiO2",
            top_clad_material="SiO2",
            film_height_um=0.18,
            ring_width_um=0.38,
            bus_width_um=0.34,
            ring_radius_um=25.0,
            gap_thru_um=0.14,
            wavelength_nm=532.0,
            span_nm=2.2,
        )
    )
    assert 1.65 < vis["metrics"]["neff_ring"] < 2.08
    assert len(vis["wavelength_warnings"]) == 0

    # 2. Datacom O-band 1310 nm SOI
    oband = simulate_mrr_topology(
        MRRDesignConfig(
            topology="point_circular_ad",
            core_material="Si",
            clad_material="SiO2",
            top_clad_material="SiO2",
            film_height_um=0.22,
            ring_width_um=0.40,
            bus_width_um=0.38,
            ring_radius_um=15.0,
            gap_thru_um=0.16,
            gap_drop_um=0.20,
            wavelength_nm=1310.0,
            span_nm=10.0,
        )
    )
    assert 2.45 < oband["metrics"]["neff_ring"] < 2.95
    assert oband["metrics"]["ng_ring"] > 3.80
    assert len(oband["wavelength_warnings"]) == 0

    # 3. Mid-IR 4200 nm Ge on CaF2
    mir = simulate_mrr_topology(
        MRRDesignConfig(
            topology="point_circular_ap",
            core_material="Ge",
            clad_material="CaF2",
            top_clad_material="Air",
            film_height_um=1.40,
            slab_height_um=0.30,
            ring_width_um=2.00,
            bus_width_um=1.80,
            ring_radius_um=65.0,
            gap_thru_um=0.40,
            wavelength_nm=4200.0,
            span_nm=35.0,
        )
    )
    assert 3.40 < mir["metrics"]["neff_ring"] < 4.05
    assert len(mir["wavelength_warnings"]) == 0

    # 4. Physical opacity warnings: c-Si at 532 nm & SiO2 cladding at 4500 nm
    bad_vis = simulate_mrr_topology(
        MRRDesignConfig(core_material="Si", wavelength_nm=532.0, film_height_um=0.18, ring_width_um=0.35, bus_width_um=0.30)
    )
    assert len(bad_vis["wavelength_warnings"]) >= 1
    assert bad_vis["metrics"]["Q_int"] < 5000


def main() -> None:
    tests = [
        ("Materials & Hardware Probe", test_materials_and_hardware),
        ("Pure-BSD Conformal FEM (Zero GPL)", test_pure_bsd_fem_no_gpl),
        ("Waveguide Width & MRR Parameter Sweeps", test_width_and_mrr_sweeps),
        ("Bidirectional GDSII Round-Trip (4 Topologies + Array)", test_bidirectional_gds_roundtrip),
        ("Conversational Photonics Copilot (EN + ZH)", test_conversational_copilot_flow),
        ("Lab Spectrum CMT Split-Doublet Fitter", test_cmt_spectrum_fitter),
        ("HTTP ASGI Endpoints & GDS Upload/Download", test_http_endpoints_and_gds_upload),
        ("Token-Minimal Codex/Claude Agent CLI & MCP Server", test_agent_tools_and_mcp_minimal_tokens),
        ("Multi-Waveband Physics (Visible 532nm / O-Band 1310nm / Mid-IR 4.2um)", test_multiband_vis_1310_midir_and_warnings),
    ]
    print("=" * 72)
    print("Running OpenMRR Studio v3.0 Full Verification Suite")
    print("=" * 72)
    for label, fn in tests:
        print(f"[RUN ] {label} ...", flush=True)
        fn()
        print(f"[PASS] {label}")
    print("=" * 72)
    print(f"ALL {len(tests)}/{len(tests)} TEST SUITES PASSED!")


if __name__ == "__main__":
    main()
