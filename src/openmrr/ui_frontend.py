"""Self-Contained Zero-CDN Native Desktop & Web UI for `OpenMRR Studio v3.0`.

Combines:
  - Left Dock: Conversational Photonics Design Copilot (English & Chinese guided spec
    interview, live parameter sweeps, 1-click critical coupling, bidirectional GDS actions)
  - Right Workbench (5 synchronized tabs):
      1. MRR Studio & Sweeps (Top-down/cross-section SVGs, broadband spectrum, coupler & sweep plots)
      2. GDS Upload & Mask Creator (Drag-drop `.gds`/`.oas` -> 2D polygon viewer + geometry extraction
         + optical simulation; Single-device & MPW Sweep-Array `.gds` + KLayout `.lyp` creator)
      3. 2D Eigenmode & Single-Mode Width Advisor (Retina `|E|` field heatmap + `n_eff(W)`/`n_g(W)` cutoff)
      4. Lab Spectrum CMT Fitter (CSV upload, BIC auto-selection: Lorentzian / Split-Doublet / Fano / Multi-FSR)
      5. 18-Material Optical Library & GPU/AMX/CPU Benchmark
"""
from __future__ import annotations

HTML_APP_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>OpenMRR Studio v3.0 — Conversational Eigenmode, CMT &amp; GDSII Designer</title>
<style>
:root {
  --bg-app: #090e1a;
  --bg-panel: #101829;
  --bg-card: #162138;
  --bg-input: #0c1322;
  --border: #253555;
  --border-hi: #38bdf8;
  --text-main: #e8eef8;
  --text-muted: #93a5c4;
  --accent: #38bdf8;
  --accent-2: #fb923c;
  --accent-3: #34d399;
  --purple: #a78bfa;
  --danger: #f87171;
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  --font-mono: "SF Mono", "Consolas", "Menlo", monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font-ui);
  background: var(--bg-app);
  color: var(--text-main);
  font-size: 12.5px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* Header */
header {
  height: 48px;
  background: linear-gradient(90deg, #0c1425 0%, #13213c 100%);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  flex-shrink: 0;
}
.brand { display: flex; align-items: center; gap: 9px; }
.brand-logo {
  width: 27px; height: 27px; border-radius: 7px;
  background: radial-gradient(circle at 30% 30%, #38bdf8, #1d4ed8);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 13px; color: #fff;
  box-shadow: 0 0 12px rgba(56,189,248,0.35);
}
.brand-title { font-weight: 700; font-size: 14.5px; letter-spacing: 0.2px; }
.brand-sub { font-size: 11px; color: var(--text-muted); margin-left: 4px; }
.nav-tabs { display: flex; gap: 5px; flex-wrap: nowrap; }
.tab-btn {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid transparent;
  padding: 5px 11px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s;
}
.tab-btn:hover { color: var(--text-main); background: rgba(255,255,255,0.04); }
.tab-btn.active {
  color: #fff;
  background: rgba(56,189,248,0.16);
  border-color: rgba(56,189,248,0.55);
}
.status-badges { display: flex; align-items: center; gap: 7px; }
.badge {
  font-size: 10.5px;
  font-family: var(--font-mono);
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--accent);
}
.badge.green { color: var(--accent-3); border-color: rgba(52,211,153,0.4); }

/* Main Split Shell: Left Copilot + Right Workbench */
.app-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

/* Left Conversational Copilot Dock */
.copilot-dock {
  width: 390px;
  min-width: 320px;
  max-width: 460px;
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: margin-left 0.2s ease;
}
.copilot-dock.collapsed {
  display: none;
}
.copilot-header {
  padding: 9px 12px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(22,33,56,0.65);
}
.copilot-title {
  font-weight: 700;
  font-size: 12.5px;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot-live {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent-3);
  box-shadow: 0 0 8px var(--accent-3);
}
.copilot-actions { display: flex; align-items: center; gap: 6px; }
.mini-btn {
  background: var(--bg-input);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 3px 8px;
  font-size: 11px;
  cursor: pointer;
}
.mini-btn:hover { border-color: var(--accent); color: #fff; }
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.msg {
  max-width: 94%;
  padding: 9px 11px;
  border-radius: 9px;
  line-height: 1.48;
  font-size: 12.2px;
  word-wrap: break-word;
}
.msg.assistant {
  align-self: flex-start;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-main);
}
.msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #0284c7, #1d4ed8);
  color: #fff;
  border: 1px solid rgba(56,189,248,0.4);
}
.msg code {
  font-family: var(--font-mono);
  font-size: 11px;
  background: rgba(9,14,26,0.65);
  padding: 1px 4px;
  border-radius: 4px;
  color: #7dd3fc;
}
.msg ul { margin: 5px 0 3px 16px; }
.msg li { margin-bottom: 3px; }
.chip-tray {
  padding: 7px 10px;
  border-top: 1px solid rgba(37,53,85,0.65);
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  max-height: 92px;
  overflow-y: auto;
  background: rgba(12,19,34,0.65);
}
.chip {
  background: rgba(56,189,248,0.10);
  color: #bae6fd;
  border: 1px solid rgba(56,189,248,0.35);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.12s;
}
.chip:hover {
  background: rgba(56,189,248,0.24);
  color: #fff;
  border-color: var(--accent);
}
.chat-composer {
  padding: 9px 10px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 6px;
  background: var(--bg-panel);
}
.chat-composer input {
  flex: 1;
  background: var(--bg-input);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 12px;
}
.chat-composer input:focus { outline: none; border-color: var(--accent); }
.send-btn {
  background: linear-gradient(135deg, #0284c7, #2563eb);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0 13px;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
}
.send-btn:disabled { opacity: 0.5; cursor: wait; }

/* Right Visual Workbench */
.workbench {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.tab-pane {
  display: none;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px;
  gap: 11px;
  flex-direction: column;
}
.tab-pane.active { display: flex; }

/* Reusable Cards, Grids & Controls */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.card-title {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
}
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}
.kpi-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 8px 10px;
}
.kpi-label { font-size: 10.5px; color: var(--text-muted); }
.kpi-val {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  margin-top: 2px;
}
.kpi-sub { font-size: 10.5px; color: var(--accent-3); margin-top: 1px; }

.param-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 7px 8px;
}
.field { display: flex; flex-direction: column; gap: 3px; }
.field label { font-size: 10.5px; color: var(--text-muted); }
.field input, .field select {
  background: var(--bg-input);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 4px 6px;
  font-size: 11.5px;
  font-family: var(--font-mono);
}
.field input:focus, .field select:focus { outline: none; border-color: var(--accent); }

.btn-row { display: flex; flex-wrap: wrap; gap: 7px; align-items: center; }
.btn {
  background: var(--bg-input);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 11px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.btn:hover { border-color: var(--accent); color: #fff; }
.btn.primary {
  background: linear-gradient(135deg, #0284c7, #2563eb);
  border-color: rgba(56,189,248,0.5);
  color: #fff;
}
.btn.amber {
  background: rgba(251,146,60,0.16);
  border-color: rgba(251,146,60,0.55);
  color: #fed7aa;
}
.btn.green {
  background: rgba(52,211,153,0.15);
  border-color: rgba(52,211,153,0.5);
  color: #a7f3d0;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.split-35-65 {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 10px;
}
canvas.plot-canvas {
  width: 100%;
  height: 235px;
  background: #080d18;
  border: 1px solid #1e2c49;
  border-radius: 6px;
  display: block;
}
canvas.gds-canvas {
  width: 100%;
  height: 360px;
  background: #060a12;
  border: 1px solid #223252;
  border-radius: 6px;
  cursor: grab;
  display: block;
}
canvas.gds-canvas:active { cursor: grabbing; }
.dropzone {
  border: 1.5px dashed rgba(56,189,248,0.45);
  background: rgba(12,19,34,0.65);
  border-radius: 7px;
  padding: 13px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}
.dropzone:hover { border-color: var(--accent); background: rgba(56,189,248,0.08); }
table.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.5px;
  font-family: var(--font-mono);
}
table.data-table th, table.data-table td {
  padding: 5px 7px;
  border-bottom: 1px solid rgba(37,53,85,0.6);
  text-align: left;
}
table.data-table th { color: var(--accent); font-weight: 600; }
details summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--accent);
  font-size: 11.5px;
  user-select: none;
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <button class="mini-btn" onclick="toggleCopilot()" title="Show/Hide AI Copilot">💬 Copilot</button>
    <div class="brand-logo">Φ</div>
    <div>
      <span class="brand-title">OpenMRR Studio</span>
      <span class="brand-sub">v3.0 · License-Free Eigenmode, CMT &amp; Bidirectional GDSII Suite</span>
    </div>
  </div>
  <div class="nav-tabs">
    <button class="tab-btn active" data-tab="tab-mrr" onclick="switchTab('tab-mrr')">1. MRR Studio &amp; Sweeps</button>
    <button class="tab-btn" data-tab="tab-gds" onclick="switchTab('tab-gds')">2. GDS Upload &amp; Mask Creator</button>
    <button class="tab-btn" data-tab="tab-mode" onclick="switchTab('tab-mode')">3. 2D Eigenmode &amp; Width Advisor</button>
    <button class="tab-btn" data-tab="tab-fit" onclick="switchTab('tab-fit')">4. Lab Spectrum CMT Fitter</button>
    <button class="tab-btn" data-tab="tab-mat" onclick="switchTab('tab-mat')">5. 24-Material &amp; GPU/CPU</button>
  </div>
  <div class="status-badges">
    <span class="badge green" id="hw-badge">Probing Compute...</span>
    <span class="badge">BSD/MIT Clean</span>
  </div>
</header>

<div class="app-shell">
  <!-- ================= LEFT DOCK: CONVERSATIONAL PHOTONICS COPILOT ================= -->
  <aside class="copilot-dock" id="copilot-dock">
    <div class="copilot-header">
      <div class="copilot-title"><span class="dot-live"></span> Photonics Design Copilot</div>
      <div class="copilot-actions">
        <label style="font-size:10.5px;color:var(--text-muted);display:flex;align-items:center;gap:3px;" title="Optional commentary from local Ollama (127.0.0.1:11434) if running">
          <input type="checkbox" id="chk-ollama"/> Ollama
        </label>
        <button class="mini-btn" onclick="document.getElementById('chat-gds-input').click()">+ .GDS</button>
        <input type="file" id="chat-gds-input" accept=".gds,.oas" style="display:none" onchange="handleGdsFileSelect(this.files[0])"/>
        <button class="mini-btn" onclick="sendChatPrompt('reset')">Reset</button>
      </div>
    </div>
    <div class="chat-messages" id="chat-messages"></div>
    <div class="chip-tray" id="chip-tray"></div>
    <div class="chat-composer">
      <input type="text" id="chat-input" placeholder="Ask e.g. '400nm Si3N4 pulley MRR, FSR 150 GHz' or '扫间距'..." onkeydown="if(event.key==='Enter') sendUserChat()"/>
      <button class="send-btn" id="chat-send-btn" onclick="sendUserChat()">Send</button>
    </div>
  </aside>

  <!-- ================= RIGHT VISUAL WORKBENCH ================= -->
  <main class="workbench">

    <!-- TAB 1: MRR STUDIO & PARAMETER SWEEPS -->
    <section class="tab-pane active" id="tab-mrr">
      <div class="kpi-strip">
        <div class="kpi-box"><div class="kpi-label">Free Spectral Range</div><div class="kpi-val" id="kpi-fsr">-- GHz</div><div class="kpi-sub" id="kpi-fsr-nm">-- nm</div></div>
        <div class="kpi-box"><div class="kpi-label">Loaded Q (Q_L)</div><div class="kpi-val" id="kpi-ql">--</div><div class="kpi-sub" id="kpi-fwhm">FWHM -- pm</div></div>
        <div class="kpi-box"><div class="kpi-label">Intrinsic / Ext Q</div><div class="kpi-val" id="kpi-qint">--</div><div class="kpi-sub" id="kpi-qext">Q_ext --</div></div>
        <div class="kpi-box"><div class="kpi-label">Extinction Ratio</div><div class="kpi-val" id="kpi-er">-- dB</div><div class="kpi-sub" id="kpi-regime">--</div></div>
        <div class="kpi-box"><div class="kpi-label">Critical-Coupling Target</div><div class="kpi-val" id="kpi-cc">--</div><div class="kpi-sub">1-click synthesis</div></div>
        <div class="kpi-box"><div class="kpi-label">EO / TO Shift</div><div class="kpi-val" id="kpi-shift">0.0 pm</div><div class="kpi-sub" id="kpi-eo-eff">n_eff / n_g</div></div>
      </div>

      <div class="card">
        <details open>
          <summary>Manual Wafer Stack, Waveband (Visible / 1310 / 1550 / Mid-IR) &amp; Resonator Controls (Live-Synced)</summary>
          <div class="param-grid" style="margin-top:9px;">
            <div class="field" style="grid-column: span 2;"><label>Topology</label><select id="cfg-topology"></select></div>
            <div class="field"><label>Core Material</label><select id="cfg-material"></select></div>
            <div class="field"><label>Bottom Clad / Sub</label>
              <select id="cfg-clad">
                <option value="SiO2">SiO2 (BOX &le;3.6 um)</option>
                <option value="CaF2">CaF2 (Mid-IR &le;9.5 um)</option>
                <option value="MgF2">MgF2 (Mid-IR &le;7.5 um)</option>
                <option value="Al2O3">Al2O3 / Sapphire (&le;5.5 um)</option>
                <option value="Si">Si (for Ge-on-Si MIR)</option>
                <option value="Air">Air / Suspended</option>
              </select>
            </div>
            <div class="field"><label>Top Cladding</label>
              <select id="cfg-topclad">
                <option value="SiO2">SiO2</option>
                <option value="Air">Air</option>
                <option value="CaF2">CaF2</option>
                <option value="MgF2">MgF2</option>
                <option value="Al2O3">Al2O3</option>
              </select>
            </div>
            <div class="field"><label>Polarization</label><select id="cfg-pol"><option value="TE0">TE0</option><option value="TM0">TM0</option></select></div>
            <div class="field"><label>Waveband Preset</label>
              <select id="cfg-band" onchange="applyWavebandPresetUI(this.value)">
                <option value="custom">Custom Wavelength</option>
                <option value="532">Visible 532 nm</option>
                <option value="633">Visible 633 nm</option>
                <option value="780">VNIR / Quantum 780 nm</option>
                <option value="1310">O-Band 1310 nm</option>
                <option value="1550" selected>C-Band 1550 nm</option>
                <option value="2000">SWIR 2000 nm</option>
                <option value="3800">Mid-IR 3800 nm</option>
                <option value="4200">Mid-IR 4200 nm (CO2)</option>
                <option value="7500">LWIR 7500 nm (Ge/Si)</option>
              </select>
            </div>
            <div class="field"><label>Wavelength [nm]</label><input type="number" id="cfg-wl" value="1550" min="350" max="14000" step="1"/></div>

            <div class="field"><label>H_film [um]</label><input type="number" id="cfg-hfilm" value="0.40" step="0.02"/></div>
            <div class="field"><label>H_slab [um]</label><input type="number" id="cfg-hslab" value="0.00" step="0.02"/></div>
            <div class="field"><label>Sidewall [deg]</label><input type="number" id="cfg-sw" value="85" step="1"/></div>
            <div class="field"><label>W_ring [um]</label><input type="number" id="cfg-wring" value="1.20" step="0.05"/></div>
            <div class="field"><label>W_bus [um]</label><input type="number" id="cfg-wbus" value="1.00" step="0.05"/></div>
            <div class="field"><label>Radius R1 [um]</label><input type="number" id="cfg-r1" value="40.0" step="2.0"/></div>
            <div class="field"><label>Gap_thru [um]</label><input type="number" id="cfg-gap" value="0.25" step="0.01"/></div>
            <div class="field"><label>L_s [um] (Racetrack)</label><input type="number" id="cfg-ls" value="12.0" step="1.0"/></div>

            <div class="field"><label>theta_pulley [deg]</label><input type="number" id="cfg-theta" value="25.0" step="2.0"/></div>
            <div class="field"><label>Loss [dB/cm]</label><input type="number" id="cfg-loss" placeholder="Auto" step="0.1"/></div>
            <div class="field"><label>Delta_T [K]</label><input type="number" id="cfg-dt" value="0.0" step="5.0"/></div>
            <div class="field"><label>Voltage [V]</label><input type="number" id="cfg-volt" value="0.0" step="2.0"/></div>
            <div class="field"><label>R2 [um] (Vernier)</label><input type="number" id="cfg-r2" value="42.5" step="0.5"/></div>
            <div class="field"><label>Span [nm]</label><input type="number" id="cfg-span" value="12.0" step="2.0"/></div>
            <div class="field" style="grid-column: span 2;">
              <label>Actions &amp; Parameter Sweeps</label>
              <div class="btn-row">
                <button class="btn primary" onclick="runManualMRR()">▶ Simulate</button>
                <button class="btn amber" onclick="sendChatPrompt('Apply critical coupling')">⚡ Crit. Couple</button>
                <button class="btn" onclick="sendChatPrompt('Sweep gap')">Sweep Gap</button>
                <button class="btn" onclick="sendChatPrompt('Export single GDS layout')">💾 .GDS</button>
                <button class="btn" onclick="exportSpectrumCSV()">📥 CSV</button>
              </div>
            </div>
          </div>
          <div id="wl-warning-bar" style="display:none;margin-top:8px;padding:6px 10px;border-radius:6px;background:rgba(248,113,113,0.14);border:1px solid rgba(248,113,113,0.5);color:#fecaca;font-size:11.5px;"></div>
        </details>
      </div>

      <div class="two-col">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Broadband Transmission Spectrum (Through &amp; Drop)</span>
            <span id="spec-status" style="font-size:11px;color:var(--text-muted);">Ready</span>
          </div>
          <canvas class="plot-canvas" id="cv-spectrum"></canvas>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title" id="sweep-plot-title">Coupler Synthesis &amp; Parameter Sweep</span>
            <span id="sweep-sub" style="font-size:11px;color:var(--accent-3);">Spatial CMT</span>
          </div>
          <canvas class="plot-canvas" id="cv-coupler"></canvas>
        </div>
      </div>

      <div class="two-col">
        <div class="card">
          <div class="card-header"><span class="card-title">Top-Down Resonator &amp; Coupler Topology</span></div>
          <div id="svg-topdown" style="height:175px;display:flex;align-items:center;justify-content:center;"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">2D Waveguide Cross-Section Stack</span></div>
          <div id="svg-xsec" style="height:175px;display:flex;align-items:center;justify-content:center;"></div>
        </div>
      </div>
    </section>

    <!-- TAB 2: BIDIRECTIONAL GDSII UPLOAD, VIEWER & MASK CREATOR -->
    <section class="tab-pane" id="tab-gds">
      <div class="two-col">
        <div class="card">
          <div class="card-header">
            <span class="card-title">A. Upload Existing .GDS / .OAS &rarr; Extract &amp; Simulate</span>
            <span style="font-size:11px;color:var(--accent-3);">gdstk + Shapely Polygon Engine</span>
          </div>
          <div class="dropzone" onclick="document.getElementById('gds-file-picker').click()"
               ondragover="event.preventDefault()"
               ondrop="event.preventDefault(); if(event.dataTransfer.files[0]) handleGdsFileSelect(event.dataTransfer.files[0]);">
            <div style="font-weight:700;color:#bae6fd;margin-bottom:4px;">Drop any `.gds` or `.oas` microring layout here (or click to browse)</div>
            <div style="font-size:11px;color:var(--text-muted);">Auto-detects Circular / Racetrack / Pulley / Dual-Ring Vernier, measures R, W_ring, W_bus, gap &amp; wrap angle</div>
            <input type="file" id="gds-file-picker" accept=".gds,.oas" style="display:none" onchange="handleGdsFileSelect(this.files[0])"/>
          </div>
          <div id="gds-extracted-box" style="margin-top:9px;font-size:11.5px;color:var(--text-muted);">
            No external GDS uploaded yet — upload a `.gds` above or generate one on the right!
          </div>
          <div class="btn-row" style="margin-top:9px;">
            <button class="btn primary" onclick="sendChatPrompt('Simulate current MRR')">▶ Simulate Extracted GDS Spectrum</button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">B. Create Foundry .GDS + KLayout .LYP Mask</span>
            <span style="font-size:11px;color:var(--text-muted);">Single Device or MPW Sweep Array</span>
          </div>
          <div class="param-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom:9px;">
            <div class="field"><label>Sweep Param</label>
              <select id="gds-sw-param">
                <option value="gap_thru_um">gap_thru_um [um]</option>
                <option value="pulley_angle_thru_deg">pulley_angle [deg]</option>
                <option value="straight_length_um">straight_L_s [um]</option>
                <option value="ring_radius_um">ring_radius [um]</option>
              </select>
            </div>
            <div class="field"><label>Start</label><input type="number" id="gds-sw-min" value="0.18" step="0.02"/></div>
            <div class="field"><label>Stop</label><input type="number" id="gds-sw-max" value="0.30" step="0.02"/></div>
            <div class="field"><label># Devices</label><input type="number" id="gds-sw-n" value="5" min="2" max="9"/></div>
          </div>
          <div class="btn-row">
            <button class="btn green" onclick="createSingleGdsUI()">💾 Create Single MRR .GDS</button>
            <button class="btn primary" onclick="createSweepArrayGdsUI()">📐 Create MPW Sweep Array .GDS</button>
          </div>
          <div id="gds-download-links" style="margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Interactive 2D GDSII Polygon &amp; Caliper Inspector (Scroll to Zoom, Drag to Pan)</span>
          <div class="btn-row">
            <span id="gds-layer-pills" style="display:flex;gap:5px;"></span>
            <button class="mini-btn" onclick="resetGdsCamera()">Fit View</button>
          </div>
        </div>
        <canvas class="gds-canvas" id="cv-gds"></canvas>
      </div>
    </section>

    <!-- TAB 3: 2D EIGENMODE & SINGLE-MODE WIDTH ADVISOR -->
    <section class="tab-pane" id="tab-mode">
      <div class="split-35-65">
        <div class="card" style="display:flex;flex-direction:column;gap:9px;">
          <div class="card-title">2D Full-Vector Eigenmode &amp; Cutoff Controls</div>
          <div class="param-grid" style="grid-template-columns: 1fr 1fr;">
            <div class="field"><label>Solver Backend</label>
              <select id="mode-backend"><option value="fem">BSD Conformal FEM</option><option value="fde">Tidy3D Yee FDE</option></select>
            </div>
            <div class="field"><label>Field Component</label>
              <select id="mode-comp" onchange="renderSelectedMode()"><option value="E_abs">|E| Total</option><option value="Ex_abs">|Ex| (TE)</option><option value="Ey_abs">|Ey| (TM)</option><option value="Ez_abs">|Ez| Longit.</option></select>
            </div>
            <div class="field"><label>Width W [um]</label><input type="number" id="mode-w" value="1.20" step="0.05"/></div>
            <div class="field"><label>Bend Radius [um] (0=∞)</label><input type="number" id="mode-r" value="40.0" step="5.0"/></div>
            <div class="field"><label>Sweep W_min [um]</label><input type="number" id="sw-wmin" value="0.50" step="0.05"/></div>
            <div class="field"><label>Sweep W_max [um]</label><input type="number" id="sw-wmax" value="2.00" step="0.05"/></div>
          </div>
          <div class="btn-row">
            <button class="btn primary" onclick="solve2DModesUI()">▶ Solve 2D Eigenmodes</button>
            <button class="btn amber" onclick="runWidthSweepUI()">📏 Width Cutoff Sweep</button>
          </div>
          <table class="data-table" id="mode-table">
            <thead><tr><th>#</th><th>n_eff</th><th>TE%</th><th>Gamma</th><th>A_eff</th></tr></thead>
            <tbody><tr><td colspan="5" style="color:var(--text-muted);">Click Solve 2D Eigenmodes or ask Copilot</td></tr></tbody>
          </table>
        </div>

        <div class="two-col" style="grid-template-columns: 1fr 1fr;">
          <div class="card">
            <div class="card-header"><span class="card-title">2D Vector Mode Profile (Inferno |E|)</span><span id="mode-meta" style="font-size:11px;color:var(--accent-3);"></span></div>
            <canvas class="plot-canvas" id="cv-mode" style="height:290px;"></canvas>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">Waveguide Width Dispersion &amp; Single-Mode Cutoff</span><span id="width-cutoff-badge" style="font-size:11px;color:var(--accent-2);"></span></div>
            <canvas class="plot-canvas" id="cv-width-sweep" style="height:290px;"></canvas>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 4: LAB SPECTRUM CMT FITTER -->
    <section class="tab-pane" id="tab-fit">
      <div class="split-35-65">
        <div class="card" style="display:flex;flex-direction:column;gap:9px;">
          <div class="card-title">Experimental MRR Spectrum CMT Fitter</div>
          <div class="dropzone" onclick="document.getElementById('csv-fit-input').click()">
            <div style="font-weight:700;color:#bae6fd;">Upload Measured `.csv` / `.txt` (wavelength_nm, transmission)</div>
            <input type="file" id="csv-fit-input" accept=".csv,.txt,.tsv" style="display:none" onchange="loadLabCsvFile(this.files[0])"/>
          </div>
          <div class="btn-row">
            <button class="mini-btn" onclick="loadDemoSpectrum('split_doublet')">Demo: Split-Doublet</button>
            <button class="mini-btn" onclick="loadDemoSpectrum('lorentzian')">Demo: Lorentzian</button>
            <button class="mini-btn" onclick="loadDemoSpectrum('fano')">Demo: Fano</button>
            <button class="mini-btn" onclick="loadDemoSpectrum('multi_fsr')">Demo: Multi-FSR n_g</button>
          </div>
          <div class="param-grid" style="grid-template-columns: 1fr 1fr;">
            <div class="field"><label>CMT Model</label>
              <select id="fit-model">
                <option value="auto">Auto BIC Selection</option>
                <option value="split_doublet">CW/CCW Split-Doublet</option>
                <option value="lorentzian">All-Pass Lorentzian</option>
                <option value="fano">Fano Interference</option>
                <option value="multi_fsr">Broadband Multi-FSR</option>
              </select>
            </div>
            <div class="field"><label>Coupling Regime</label>
              <select id="fit-regime"><option value="">Unconstrained</option><option value="undercoupled">Undercoupled</option><option value="overcoupled">Overcoupled</option></select>
            </div>
            <div class="field" style="grid-column:span 2;"><label>Cavity Round-Trip Length L_rt [um]</label><input type="number" id="fit-lrt" value="263.89" step="1.0"/></div>
          </div>
          <button class="btn primary" onclick="runCmtFitUI()">▶ Run CMT Parameter Extraction</button>
          <div id="fit-results-box" style="font-family:var(--font-mono);font-size:11.5px;line-height:1.55;color:var(--text-main);"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Measured Transmission vs Analytical CMT Fit</span></div>
          <canvas class="plot-canvas" id="cv-fit" style="height:330px;"></canvas>
        </div>
      </div>
    </section>

    <!-- TAB 5: 18-MATERIAL LIBRARY & GPU/CPU ENGINE -->
    <section class="tab-pane" id="tab-mat">
      <div class="two-col">
        <div class="card">
          <div class="card-header">
            <span class="card-title">24 Clean-Room Photonics Materials Dispersion (Visible 400 nm &rarr; Mid-IR 14 &mu;m)</span>
            <select id="mat-browser-sel" onchange="loadMaterialCurve()" style="background:var(--bg-input);color:#fff;border:1px solid var(--border);border-radius:4px;padding:3px 7px;"></select>
          </div>
          <canvas class="plot-canvas" id="cv-mat" style="height:240px;"></canvas>
          <div id="mat-props-text" style="margin-top:8px;font-size:11.5px;color:var(--text-muted);font-family:var(--font-mono);"></div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Auto-Probed Compute Engine (Apple Silicon / NVIDIA CUDA / CPU)</span>
            <button class="btn primary" onclick="runBenchmarkUI()">⚡ Run 100k-pt Benchmark</button>
          </div>
          <div id="hw-detail-box" style="font-family:var(--font-mono);font-size:12px;line-height:1.65;padding:8px 0;"></div>
        </div>
      </div>
    </section>

  </main>
</div>

<script>
// ==================== GLOBAL STATE ====================
let copilotSession = null;
let catalogMaterials = [];
let catalogTopologies = {};
let lastMrrResult = null;
let lastModesData = null;
let selectedModeIdx = 0;
let lastWidthSweep = null;
let labSpectrumData = null;
let currentGdsView = null;
let gdsCam = { scale: 1.0, offsetX: 0, offsetY: 0, dragging: false, lastX: 0, lastY: 0, hiddenLayers: {} };

const LAYER_COLORS = {
  "1/0": "#38bdf8",
  "2/0": "#0284c7",
  "10/0": "#f59e0b",
  "11/0": "#eab308",
  "65/0": "#34d399",
  "66/0": "#e2e8f0"
};

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === tabId));
  if (tabId === 'tab-gds' && currentGdsView) setTimeout(drawGdsCanvas, 30);
  if (tabId === 'tab-mrr' && lastMrrResult) setTimeout(() => renderMrrResult(lastMrrResult), 30);
}

function toggleCopilot() {
  document.getElementById('copilot-dock').classList.toggle('collapsed');
}

// ==================== MARKDOWN MINI-FORMATTER ====================
function fmtMd(raw) {
  let s = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  const lines = s.split('\n');
  let out = [], inList = false;
  for (const ln of lines) {
    if (ln.trim().startsWith('- ')) {
      if (!inList) { out.push('<ul>'); inList = true; }
      out.push('<li>' + ln.trim().slice(2) + '</li>');
    } else {
      if (inList) { out.push('</ul>'); inList = false; }
      if (ln.trim() === '') out.push('<div style="height:5px"></div>');
      else out.push('<div>' + ln + '</div>');
    }
  }
  if (inList) out.push('</ul>');
  return out.join('');
}

function appendChatBubble(role, text) {
  const box = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = role === 'assistant' ? fmtMd(text) : text.replace(/</g, '&lt;');
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function renderChips(chips) {
  const tray = document.getElementById('chip-tray');
  tray.innerHTML = '';
  (chips || []).forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.textContent = c.label;
    btn.onclick = () => sendChatPrompt(c.prompt);
    tray.appendChild(btn);
  });
}

// ==================== SYNC CONFIG <-> FORM ====================
function syncFormFromConfig(cfg) {
  if (!cfg) return;
  const setVal = (id, v) => { const el = document.getElementById(id); if (el && v !== undefined && v !== null) el.value = v; };
  setVal('cfg-topology', cfg.topology);
  setVal('cfg-material', cfg.core_material);
  setVal('cfg-clad', cfg.clad_material || 'SiO2');
  setVal('cfg-topclad', cfg.top_clad_material);
  setVal('cfg-pol', cfg.polarization);
  setVal('cfg-wl', cfg.wavelength_nm);
  const bandEl = document.getElementById('cfg-band');
  if (bandEl && cfg.wavelength_nm !== undefined) {
    const known = ['532', '633', '780', '1310', '1550', '2000', '3800', '4200', '7500'];
    const sWl = String(Math.round(cfg.wavelength_nm));
    bandEl.value = known.includes(sWl) ? sWl : 'custom';
  }
  setVal('cfg-hfilm', cfg.film_height_um);
  setVal('cfg-hslab', cfg.slab_height_um);
  setVal('cfg-sw', cfg.sidewall_deg);
  setVal('cfg-wring', cfg.ring_width_um);
  setVal('cfg-wbus', cfg.bus_width_um);
  setVal('cfg-r1', cfg.ring_radius_um);
  setVal('cfg-gap', cfg.gap_thru_um);
  setVal('cfg-ls', cfg.straight_length_um);
  setVal('cfg-theta', cfg.pulley_angle_thru_deg);
  setVal('cfg-dt', cfg.delta_temp_k);
  setVal('cfg-volt', cfg.voltage_v);
  setVal('cfg-r2', cfg.ring2_radius_um);
  setVal('cfg-span', cfg.span_nm);
  setVal('mode-w', cfg.ring_width_um);
  setVal('mode-r', cfg.ring_radius_um);
  renderSchematicsSVG(cfg);
}

function applyWavebandPresetUI(val) {
  if (val === 'custom') return;
  const wl = parseFloat(val);
  document.getElementById('cfg-wl').value = wl;
  let curMat = document.getElementById('cfg-material').value;
  // Auto-select transparent core/cladding & physical single-mode geometry for chosen waveband
  if (wl < 1050 && (curMat === 'Si' || curMat === 'Ge' || curMat === 'a-Si')) {
    curMat = 'Si3N4';
    document.getElementById('cfg-material').value = 'Si3N4';
  } else if (wl > 5500 && curMat !== 'Ge' && curMat !== 'Diamond') {
    curMat = 'Ge';
    document.getElementById('cfg-material').value = 'Ge';
  }
  if (wl > 3650) {
    document.getElementById('cfg-clad').value = (wl > 5500 && curMat === 'Ge') ? 'Si' : 'CaF2';
    document.getElementById('cfg-topclad').value = 'Air';
  } else {
    document.getElementById('cfg-clad').value = 'SiO2';
    document.getElementById('cfg-topclad').value = 'SiO2';
  }
  const r = wl / 1550.0;
  document.getElementById('cfg-hfilm').value = (curMat === 'Si' && wl >= 1200 && wl <= 1680) ? 0.22 : Math.max(0.14, +(0.38 * Math.pow(r, 0.88)).toFixed(2));
  document.getElementById('cfg-wring').value = Math.max(0.28, +(((curMat === 'Si') ? 0.48 : 1.05) * Math.pow(r, 0.88)).toFixed(2));
  document.getElementById('cfg-wbus').value = Math.max(0.24, +(((curMat === 'Si') ? 0.42 : 0.90) * Math.pow(r, 0.88)).toFixed(2));
  document.getElementById('cfg-gap').value = Math.max(0.12, +(0.24 * Math.pow(r, 0.65)).toFixed(2));
  document.getElementById('cfg-span').value = Math.max(2.0, +(12.0 * Math.pow(r, 1.80)).toFixed(1));
  runManualMRR();
}

function readConfigFromForm() {
  const num = (id, fb) => { const v = parseFloat(document.getElementById(id).value); return Number.isFinite(v) ? v : fb; };
  const lossRaw = document.getElementById('cfg-loss').value;
  return {
    topology: document.getElementById('cfg-topology').value,
    core_material: document.getElementById('cfg-material').value,
    clad_material: (document.getElementById('cfg-clad') && document.getElementById('cfg-clad').value) || 'SiO2',
    top_clad_material: document.getElementById('cfg-topclad').value,
    polarization: document.getElementById('cfg-pol').value,
    wavelength_nm: num('cfg-wl', 1550),
    film_height_um: num('cfg-hfilm', 0.40),
    slab_height_um: num('cfg-hslab', 0.0),
    sidewall_deg: num('cfg-sw', 85),
    ring_width_um: num('cfg-wring', 1.20),
    bus_width_um: num('cfg-wbus', 1.00),
    ring_radius_um: num('cfg-r1', 40.0),
    gap_thru_um: num('cfg-gap', 0.25),
    gap_drop_um: num('cfg-gap', 0.25),
    straight_length_um: num('cfg-ls', 12.0),
    pulley_angle_thru_deg: num('cfg-theta', 25.0),
    pulley_angle_drop_deg: num('cfg-theta', 25.0),
    delta_temp_k: num('cfg-dt', 0.0),
    voltage_v: num('cfg-volt', 0.0),
    ring2_radius_um: num('cfg-r2', 42.5),
    span_nm: num('cfg-span', 12.0),
    alpha_loss_db_per_cm: lossRaw === '' ? null : parseFloat(lossRaw)
  };
}

// ==================== CHATBOT API ====================
async function initChat() {
  const r = await fetch('/api/chat_init', { method: 'POST' });
  const data = await r.json();
  copilotSession = data.session;
  document.getElementById('chat-messages').innerHTML = '';
  appendChatBubble('assistant', data.assistant_message);
  renderChips(data.chips);
  syncFormFromConfig(copilotSession.config);
}

async function sendUserChat() {
  const inp = document.getElementById('chat-input');
  const txt = inp.value.trim();
  if (!txt) return;
  inp.value = '';
  await sendChatPrompt(txt);
}

async function sendChatPrompt(promptText) {
  const btn = document.getElementById('chat-send-btn');
  btn.disabled = true;
  if (promptText.toLowerCase() !== 'reset') appendChatBubble('user', promptText);
  const thinking = appendChatBubble('assistant', 'Solving Maxwell eigenmodes / CMT...');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session: copilotSession,
        message: promptText,
        use_ollama: document.getElementById('chk-ollama').checked
      })
    });
    const data = await r.json();
    thinking.remove();
    if (data.error) {
      appendChatBubble('assistant', '**Solver Error**: `' + data.error + '`');
      return;
    }
    copilotSession = data.session;
    if (promptText.toLowerCase() === 'reset') document.getElementById('chat-messages').innerHTML = '';
    appendChatBubble('assistant', data.assistant_message);
    renderChips(data.chips);
    syncFormFromConfig(copilotSession.config);

    if (data.active_tab) switchTab(data.active_tab);
    if (data.mrr_result) {
      lastMrrResult = data.mrr_result;
      renderMrrResult(data.mrr_result);
    }
    if (data.width_sweep_result) {
      lastWidthSweep = data.width_sweep_result;
      drawWidthSweepPlot(data.width_sweep_result);
      solve2DModesUI();
    }
    if (data.mrr_sweep_result) {
      drawMrrSweepPlot(data.mrr_sweep_result);
    }
    if (data.gds_export) {
      showGdsExportResult(data.gds_export);
    }
  } catch (err) {
    thinking.remove();
    appendChatBubble('assistant', 'Request failed: `' + err + '`');
  } finally {
    btn.disabled = false;
  }
}

// ==================== RETINA CANVAS PLOTTING HELPERS ====================
function setupCanvas(id) {
  const cv = document.getElementById(id);
  const dpr = window.devicePixelRatio || 2;
  const rect = cv.getBoundingClientRect();
  const w = Math.max(rect.width, 320);
  const h = Math.max(rect.height, 200);
  cv.width = Math.round(w * dpr);
  cv.height = Math.round(h * dpr);
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { cv, ctx, w, h };
}

function drawLinePlot(canvasId, seriesList, xLabel, yLabel, vLineX = null) {
  const { ctx, w, h } = setupCanvas(canvasId);
  ctx.fillStyle = '#080d18';
  ctx.fillRect(0, 0, w, h);
  const pad = { l: 52, r: 18, t: 18, b: 34 };
  const pw = w - pad.l - pad.r, ph = h - pad.t - pad.b;

  let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
  seriesList.forEach(s => {
    for (let i = 0; i < s.x.length; i++) {
      const xv = s.x[i], yv = s.y[i];
      if (yv === null || yv === undefined || !Number.isFinite(yv)) continue;
      if (xv < xmin) xmin = xv; if (xv > xmax) xmax = xv;
      if (yv < ymin) ymin = yv; if (yv > ymax) ymax = yv;
    }
  });
  if (!Number.isFinite(xmin)) return;
  if (Math.abs(ymax - ymin) < 1e-9) { ymax += 1; ymin -= 1; }
  const ym = 0.07 * (ymax - ymin); ymin -= ym; ymax += ym;

  const sx = x => pad.l + ((x - xmin) / (xmax - xmin || 1)) * pw;
  const sy = y => pad.t + ph - ((y - ymin) / (ymax - ymin || 1)) * ph;

  // 4-sided closed box + inward ticks (Nature Photonics style)
  ctx.strokeStyle = '#3b4f78';
  ctx.lineWidth = 1.1;
  ctx.strokeRect(pad.l, pad.t, pw, ph);

  ctx.fillStyle = '#93a5c4';
  ctx.font = '10.5px Arial, sans-serif';
  for (let i = 0; i <= 4; i++) {
    const tx = pad.l + (i / 4) * pw;
    const vx = xmin + (i / 4) * (xmax - xmin);
    ctx.beginPath(); ctx.moveTo(tx, pad.t + ph); ctx.lineTo(tx, pad.t + ph - 5); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(tx, pad.t); ctx.lineTo(tx, pad.t + 5); ctx.stroke();
    ctx.textAlign = 'center';
    ctx.fillText(vx.toFixed(Math.abs(xmax - xmin) < 1 ? 3 : 2), tx, h - 18);

    const ty = pad.t + ph - (i / 4) * ph;
    const vy = ymin + (i / 4) * (ymax - ymin);
    ctx.beginPath(); ctx.moveTo(pad.l, ty); ctx.lineTo(pad.l + 5, ty); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pad.l + pw, ty); ctx.lineTo(pad.l + pw - 5, ty); ctx.stroke();
    ctx.textAlign = 'right';
    ctx.fillText(vy.toFixed(Math.abs(ymax - ymin) < 2 ? 2 : 1), pad.l - 6, ty + 3.5);
  }

  if (vLineX !== null && vLineX >= xmin && vLineX <= xmax) {
    const vx = sx(vLineX);
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = '#fb923c';
    ctx.beginPath(); ctx.moveTo(vx, pad.t); ctx.lineTo(vx, pad.t + ph); ctx.stroke();
    ctx.restore();
  }

  seriesList.forEach((s, idx) => {
    ctx.strokeStyle = s.color || '#38bdf8';
    ctx.lineWidth = s.width || 1.6;
    if (s.dashed) ctx.setLineDash([4, 3]); else ctx.setLineDash([]);
    ctx.beginPath();
    let started = false;
    for (let i = 0; i < s.x.length; i++) {
      const yv = s.y[i];
      if (yv === null || yv === undefined || !Number.isFinite(yv)) { started = false; continue; }
      const px = sx(s.x[i]), py = sy(yv);
      if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    if (s.dots) {
      ctx.fillStyle = s.color || '#38bdf8';
      for (let i = 0; i < s.x.length; i++) {
        if (s.y[i] === null || !Number.isFinite(s.y[i])) continue;
        ctx.beginPath(); ctx.arc(sx(s.x[i]), sy(s.y[i]), 2.6, 0, Math.PI * 2); ctx.fill();
      }
    }
    if (s.label) {
      ctx.fillStyle = s.color;
      ctx.textAlign = 'left';
      ctx.font = 'bold 10.5px Arial';
      ctx.fillText(s.label, pad.l + 10 + idx * 125, pad.t + 14);
    }
  });

  ctx.fillStyle = '#cbd5e1';
  ctx.textAlign = 'center';
  ctx.font = '11px Arial';
  ctx.fillText(xLabel, pad.l + pw / 2, h - 4);
  ctx.save();
  ctx.translate(13, pad.t + ph / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();
}

// ==================== MRR SIMULATION & SCHEMATICS ====================
async function runManualMRR() {
  const cfg = readConfigFromForm();
  if (copilotSession) copilotSession.config = Object.assign(copilotSession.config || {}, cfg);
  document.getElementById('spec-status').textContent = 'Solving 2D FEM + CMT...';
  const r = await fetch('/api/design_mrr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg)
  });
  const data = await r.json();
  if (data.error) {
    document.getElementById('spec-status').textContent = 'Error: ' + data.error;
    return;
  }
  lastMrrResult = data;
  renderMrrResult(data);
  document.getElementById('spec-status').textContent = `Solved in ${data.elapsed_ms} ms`;
}

function renderMrrResult(res) {
  const m = res.metrics;
  const cc = res.critical_coupling;
  const wBar = document.getElementById('wl-warning-bar');
  if (wBar) {
    const warns = res.wavelength_warnings || [];
    if (warns.length > 0) {
      wBar.style.display = 'block';
      wBar.textContent = '⚠ ' + warns.join(' | ');
    } else {
      wBar.style.display = 'none';
    }
  }
  document.getElementById('kpi-fsr').textContent = `${m.FSR_GHz.toFixed(2)} GHz`;
  document.getElementById('kpi-fsr-nm').textContent = `${m.FSR_nm.toFixed(3)} nm`;
  document.getElementById('kpi-ql').textContent = Math.round(m.Q_loaded).toLocaleString();
  document.getElementById('kpi-fwhm').textContent = `FWHM ${m.FWHM_pm.toFixed(2)} pm`;
  document.getElementById('kpi-qint').textContent = Math.round(m.Q_int).toLocaleString();
  document.getElementById('kpi-qext').textContent = `Q_ext ${Math.round(m.Q_ext_thru).toLocaleString()}`;
  document.getElementById('kpi-er').textContent = `${m.ER_thru_dB.toFixed(1)} dB`;
  document.getElementById('kpi-regime').textContent = cc.regime;
  document.getElementById('kpi-cc').textContent = `${cc.recommended_value} ${cc.unit}`;
  document.getElementById('kpi-shift').textContent = `${(m.tuning_shift_pm || 0).toFixed(1)} pm`;
  document.getElementById('kpi-eo-eff').textContent = `n_eff=${m.neff_ring.toFixed(4)} | n_g=${m.ng_ring.toFixed(4)}`;

  const sp = res.spectrum;
  const series = [{ x: sp.wavelength_nm, y: sp.thru_dB, color: '#38bdf8', label: 'Through [dB]' }];
  if (sp.drop_dB && sp.drop_dB.some(v => v > -59.5)) {
    series.push({ x: sp.wavelength_nm, y: sp.drop_dB, color: '#fb923c', label: 'Drop [dB]' });
  }
  drawLinePlot('cv-spectrum', series, 'Wavelength [nm]', 'Transmission [dB]');

  if (res.coupler_curve) {
    const c = res.coupler_curve;
    document.getElementById('sweep-plot-title').textContent = 'Coupler Synthesis Curve';
    drawLinePlot(
      'cv-coupler',
      [{ x: c.x_values, y: c.log10_Q_ext, color: '#34d399', label: 'log10(Q_ext)' }],
      `${c.x_param} [${c.x_unit}]`,
      'log10(Q_ext)',
      cc.recommended_value
    );
  }
  renderSchematicsSVG(res.config || readConfigFromForm());
}

function drawMrrSweepPlot(sw) {
  document.getElementById('sweep-plot-title').textContent = `Sweep: ${sw.param_name} [${sw.unit}]`;
  document.getElementById('sweep-sub').textContent = `Peak ER = ${Math.max(...sw.ER_thru_dB).toFixed(1)} dB`;
  drawLinePlot(
    'cv-coupler',
    [{ x: sw.values, y: sw.ER_thru_dB, color: '#fb923c', dots: true, label: 'Extinction Ratio [dB]' }],
    `${sw.param_name} [${sw.unit}]`,
    'Through ER [dB]',
    sw.values[sw.best_critical_coupling_index]
  );
}

function renderSchematicsSVG(cfg) {
  const t = cfg.topology || 'point_circular_ap';
  const is4 = t.endsWith('_ad');
  const isRace = t.startsWith('racetrack');
  const isPulley = t.startsWith('pulley');
  const isVernier = t === 'vernier_crow_ad';

  let ringSvg = '';
  if (isVernier) {
    ringSvg = `<circle cx="155" cy="85" r="34" fill="none" stroke="#38bdf8" stroke-width="5"/>
               <circle cx="231" cy="85" r="36" fill="none" stroke="#a78bfa" stroke-width="5"/>
               <line x1="35" y1="127" x2="345" y2="127" stroke="#34d399" stroke-width="4"/>
               <line x1="35" y1="41" x2="345" y2="41" stroke="#fb923c" stroke-width="4"/>`;
  } else if (isRace) {
    ringSvg = `<rect x="125" y="48" width="130" height="74" rx="37" fill="none" stroke="#38bdf8" stroke-width="5"/>
               <line x1="35" y1="130" x2="345" y2="130" stroke="#34d399" stroke-width="4"/>` +
               (is4 ? `<line x1="35" y1="40" x2="345" y2="40" stroke="#fb923c" stroke-width="4"/>` : '');
  } else if (isPulley) {
    ringSvg = `<circle cx="190" cy="85" r="42" fill="none" stroke="#38bdf8" stroke-width="5"/>
               <path d="M 40 142 L 135 142 Q 190 122 245 142 L 340 142" fill="none" stroke="#34d399" stroke-width="4"/>` +
               (is4 ? `<path d="M 40 28 L 135 28 Q 190 48 245 28 L 340 28" fill="none" stroke="#fb923c" stroke-width="4"/>` : '');
  } else {
    ringSvg = `<circle cx="190" cy="85" r="42" fill="none" stroke="#38bdf8" stroke-width="5"/>
               <line x1="35" y1="134" x2="345" y2="134" stroke="#34d399" stroke-width="4"/>` +
               (is4 ? `<line x1="35" y1="36" x2="345" y2="36" stroke="#fb923c" stroke-width="4"/>` : '');
  }
  document.getElementById('svg-topdown').innerHTML = `
    <svg width="380" height="168" viewBox="0 0 380 168">
      <rect width="380" height="168" rx="6" fill="#080d18"/>
      ${ringSvg}
      <text x="12" y="158" fill="#93a5c4" font-size="11" font-family="monospace">${t} | R=${cfg.ring_radius_um} um | gap=${Math.round((cfg.gap_thru_um||0.25)*1000)} nm</text>
    </svg>`;

  const hSlabRatio = Math.min(0.75, (cfg.slab_height_um || 0) / Math.max(cfg.film_height_um || 0.4, 0.05));
  const coreH = 54, slabH = Math.round(coreH * hSlabRatio);
  document.getElementById('svg-xsec').innerHTML = `
    <svg width="380" height="168" viewBox="0 0 380 168">
      <rect width="380" height="168" rx="6" fill="#080d18"/>
      <rect x="25" y="112" width="330" height="38" fill="#1e293b"/>
      <rect x="25" y="24" width="330" height="88" fill="${cfg.top_clad_material==='Air'?'#0b1324':'#172554'}" opacity="0.7"/>
      ${slabH > 0 ? `<rect x="40" y="${112 - slabH}" width="300" height="${slabH}" fill="#0284c7"/>` : ''}
      <polygon points="135,112 245,112 236,${112 - coreH} 144,${112 - coreH}" fill="#38bdf8" stroke="#bae6fd" stroke-width="1"/>
      <text x="190" y="${112 - coreH/2 + 4}" text-anchor="middle" fill="#080d18" font-weight="bold" font-size="11">${cfg.core_material}</text>
      <text x="12" y="158" fill="#93a5c4" font-size="11" font-family="monospace">W=${cfg.ring_width_um} um | H=${Math.round((cfg.film_height_um||0.4)*1000)} nm | slab=${Math.round((cfg.slab_height_um||0)*1000)} nm | ${cfg.sidewall_deg}°</text>
    </svg>`;
}

// ==================== BIDIRECTIONAL GDSII UPLOAD & CREATOR ====================
function handleGdsFileSelect(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async () => {
    const b64 = reader.result.split(',')[1] || reader.result;
    const r = await fetch('/api/upload_gds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: file.name, content_b64: b64, session: copilotSession })
    });
    const data = await r.json();
    if (data.error) {
      alert('GDS Parse Error: ' + data.error);
      return;
    }
    copilotSession = data.session;
    appendChatBubble('assistant', data.assistant_message);
    renderChips(data.chips);
    syncFormFromConfig(copilotSession.config);
    switchTab('tab-gds');
    setGdsView(data.gds_info);
  };
  reader.readAsDataURL(file);
}

function setGdsView(gdsInfo) {
  currentGdsView = gdsInfo;
  gdsCam.hiddenLayers = {};
  const ext = gdsInfo.extracted_geometry;
  document.getElementById('gds-extracted-box').innerHTML = `
    <div style="color:#e2e8f0;line-height:1.55;">
      <strong>File</strong>: <code>${gdsInfo.file_name}</code> (Cell: <code>${gdsInfo.cell_name}</code>, Core Layer: <code>${gdsInfo.selected_core_layer.join('/')}</code>)<br/>
      <strong>Detected</strong>: <span style="color:#38bdf8;font-weight:700;">${ext.topology_display}</span> (${ext.ports_detected}-Port)<br/>
      <strong>Polygon Measurements</strong>: R = <code>${ext.ring_radius_um} um</code> | W_ring = <code>${ext.ring_width_um} um</code> | W_bus = <code>${ext.bus_width_um} um</code> | gap_thru = <strong style="color:#34d399;">${(ext.gap_thru_um*1000).toFixed(1)} nm</strong>
      ${ext.straight_length_um > 0 ? ` | L_s = <code>${ext.straight_length_um} um</code>` : ''}
      ${ext.topology.includes('pulley') ? ` | theta = <code>${ext.pulley_angle_thru_deg} deg</code>` : ''}
    </div>`;

  const pills = document.getElementById('gds-layer-pills');
  pills.innerHTML = '';
  gdsInfo.viewer_layers.forEach(vl => {
    const key = `${vl.layer}/${vl.datatype}`;
    const col = LAYER_COLORS[key] || '#a78bfa';
    const b = document.createElement('button');
    b.className = 'mini-btn';
    b.style.borderColor = col;
    b.style.color = col;
    b.textContent = `L ${key}`;
    b.onclick = () => {
      gdsCam.hiddenLayers[key] = !gdsCam.hiddenLayers[key];
      b.style.opacity = gdsCam.hiddenLayers[key] ? '0.35' : '1.0';
      drawGdsCanvas();
    };
    pills.appendChild(b);
  });
  resetGdsCamera();
}

function showGdsExportResult(exp) {
  const dl = document.getElementById('gds-download-links');
  dl.innerHTML = `
    <a class="btn green" href="${exp.gds_download_url}" download>⬇ Download .GDS Mask</a>
    <a class="btn amber" href="${exp.lyp_download_url}" download>⬇ Download KLayout .LYP</a>
    <span style="font-size:11px;color:var(--text-muted);font-family:var(--font-mono);">Saved: ${exp.gds_path || exp.saved_path}</span>`;
  if (exp.gds_view) setGdsView(exp.gds_view);
}

async function createSingleGdsUI() {
  const cfg = readConfigFromForm();
  const r = await fetch('/api/export_gds', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg)
  });
  const data = await r.json();
  if (!data.error) showGdsExportResult(data);
}

async function createSweepArrayGdsUI() {
  const cfg = readConfigFromForm();
  const payload = {
    config: cfg,
    param_name: document.getElementById('gds-sw-param').value,
    v_min: parseFloat(document.getElementById('gds-sw-min').value),
    v_max: parseFloat(document.getElementById('gds-sw-max').value),
    num_devices: parseInt(document.getElementById('gds-sw-n').value, 10)
  };
  const r = await fetch('/api/export_sweep_gds', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (!data.error) showGdsExportResult(data);
}

function resetGdsCamera() {
  gdsCam.scale = 1.0; gdsCam.offsetX = 0; gdsCam.offsetY = 0;
  drawGdsCanvas();
}

function drawGdsCanvas() {
  if (!currentGdsView) return;
  const { cv, ctx, w, h } = setupCanvas('cv-gds');
  ctx.fillStyle = '#060a12';
  ctx.fillRect(0, 0, w, h);

  const [xmin, ymin, xmax, ymax] = currentGdsView.bbox_um;
  const spanX = Math.max(xmax - xmin, 1.0), spanY = Math.max(ymax - ymin, 1.0);
  const baseScale = 0.84 * Math.min(w / spanX, h / spanY) * gdsCam.scale;
  const cx = 0.5 * (xmin + xmax), cy = 0.5 * (ymin + ymax);
  const tx = x => w / 2 + (x - cx) * baseScale + gdsCam.offsetX;
  const ty = y => h / 2 - (y - cy) * baseScale + gdsCam.offsetY;

  currentGdsView.viewer_layers.forEach(vl => {
    const key = `${vl.layer}/${vl.datatype}`;
    if (gdsCam.hiddenLayers[key]) return;
    const col = LAYER_COLORS[key] || '#a78bfa';
    ctx.fillStyle = col + '44';
    ctx.strokeStyle = col;
    ctx.lineWidth = vl.is_core ? 1.35 : 0.9;
    vl.polygons.forEach(pts => {
      if (pts.length < 3) return;
      ctx.beginPath();
      ctx.moveTo(tx(pts[0][0]), ty(pts[0][1]));
      for (let i = 1; i < pts.length; i++) ctx.lineTo(tx(pts[i][0]), ty(pts[i][1]));
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  });

  // Draw red gap measurement calipers
  (currentGdsView.gap_markers || []).forEach(gm => {
    const x1 = tx(gm.ring_pt[0]), y1 = ty(gm.ring_pt[1]);
    const x2 = tx(gm.bus_pt[0]), y2 = ty(gm.bus_pt[1]);
    ctx.strokeStyle = '#f87171';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.fillStyle = '#fecaca';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`gap = ${(gm.gap_um * 1000).toFixed(1)} nm`, 0.5 * (x1 + x2) + 8, 0.5 * (y1 + y2) - 5);
  });
}

// Mouse pan & zoom on GDS canvas
(function attachGdsEvents() {
  const cv = document.getElementById('cv-gds');
  cv.addEventListener('wheel', e => {
    e.preventDefault();
    gdsCam.scale *= (e.deltaY < 0 ? 1.18 : 0.85);
    gdsCam.scale = Math.max(0.2, Math.min(40, gdsCam.scale));
    drawGdsCanvas();
  }, { passive: false });
  cv.addEventListener('mousedown', e => { gdsCam.dragging = true; gdsCam.lastX = e.clientX; gdsCam.lastY = e.clientY; });
  window.addEventListener('mouseup', () => { gdsCam.dragging = false; });
  window.addEventListener('mousemove', e => {
    if (!gdsCam.dragging) return;
    gdsCam.offsetX += (e.clientX - gdsCam.lastX);
    gdsCam.offsetY += (e.clientY - gdsCam.lastY);
    gdsCam.lastX = e.clientX; gdsCam.lastY = e.clientY;
    drawGdsCanvas();
  });
})();

// ==================== TAB 3: 2D EIGENMODE & WIDTH CUTOFF ====================
async function solve2DModesUI() {
  const cfg = readConfigFromForm();
  const payload = {
    core_material: cfg.core_material,
    clad_material: cfg.clad_material,
    top_clad_material: cfg.top_clad_material,
    w_bottom_um: parseFloat(document.getElementById('mode-w').value) || cfg.ring_width_um,
    h_film_um: cfg.film_height_um,
    h_slab_um: cfg.slab_height_um,
    sidewall_deg: cfg.sidewall_deg,
    wavelength_nm: cfg.wavelength_nm,
    bend_radius_um: parseFloat(document.getElementById('mode-r').value) || 0,
    solver_backend: document.getElementById('mode-backend').value,
    num_modes: 4
  };
  const r = await fetch('/api/solve_mode', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (data.error) return;
  lastModesData = data;
  selectedModeIdx = 0;
  const tbody = document.querySelector('#mode-table tbody');
  tbody.innerHTML = '';
  data.modes.forEach((m, i) => {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => { selectedModeIdx = i; renderSelectedMode(); };
    tr.innerHTML = `<td>M${i}</td><td>${m.n_eff_real.toFixed(5)}</td><td>${(m.te_fraction*100).toFixed(1)}%</td><td>${(m.core_confinement*100).toFixed(1)}%</td><td>${m.a_eff_um2.toFixed(3)}</td>`;
    tbody.appendChild(tr);
  });
  renderSelectedMode();
}

function infernoColor(t) {
  const c = Math.max(0, Math.min(1, t));
  const r = Math.round(255 * Math.min(1, Math.pow(c, 0.65) * 1.25));
  const g = Math.round(255 * Math.pow(c, 1.85));
  const b = Math.round(255 * (c < 0.5 ? c * 1.4 : Math.max(0, 1.4 - c * 1.5)));
  return [r, g, b];
}

function renderSelectedMode() {
  if (!lastModesData || !lastModesData.modes.length) return;
  const m = lastModesData.modes[selectedModeIdx];
  const comp = document.getElementById('mode-comp').value;
  const grid = m[comp];
  document.getElementById('mode-meta').textContent = `n_eff = ${m.n_eff_real.toFixed(5)} | TE ${(m.te_fraction*100).toFixed(1)}%`;

  const { ctx, w, h } = setupCanvas('cv-mode');
  ctx.fillStyle = '#050811';
  ctx.fillRect(0, 0, w, h);
  const pad = { l: 42, r: 14, t: 14, b: 28 };
  const pw = w - pad.l - pad.r, ph = h - pad.t - pad.b;
  const ny = grid.length, nx = grid[0].length;
  let vmax = 1e-9;
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) if (grid[j][i] > vmax) vmax = grid[j][i];

  const off = document.createElement('canvas');
  off.width = nx; off.height = ny;
  const octx = off.getContext('2d');
  const img = octx.createImageData(nx, ny);
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const [r, g, b] = infernoColor(grid[ny - 1 - j][i] / vmax);
      const k = 4 * (j * nx + i);
      img.data[k] = r; img.data[k+1] = g; img.data[k+2] = b; img.data[k+3] = 255;
    }
  }
  octx.putImageData(img, 0, 0);
  ctx.drawImage(off, pad.l, pad.t, pw, ph);

  const xs = m.x_um, ys = m.y_um;
  const xmin = xs[0], xmax = xs[xs.length - 1], ymin = ys[0], ymax = ys[ys.length - 1];
  ctx.strokeStyle = 'rgba(255,255,255,0.85)';
  ctx.lineWidth = 1.3;
  (lastModesData.polygon_outlines_um || []).forEach(poly => {
    ctx.beginPath();
    poly.forEach(([px, py], idx) => {
      const cx = pad.l + ((px - xmin) / (xmax - xmin)) * pw;
      const cy = pad.t + ph - ((py - ymin) / (ymax - ymin)) * ph;
      if (idx === 0) ctx.moveTo(cx, cy); else ctx.lineTo(cx, cy);
    });
    ctx.closePath();
    ctx.stroke();
  });
}

async function runWidthSweepUI() {
  const cfg = readConfigFromForm();
  const payload = {
    core_material: cfg.core_material,
    clad_material: cfg.clad_material,
    top_clad_material: cfg.top_clad_material,
    h_film_um: cfg.film_height_um,
    h_slab_um: cfg.slab_height_um,
    sidewall_deg: cfg.sidewall_deg,
    wavelength_nm: cfg.wavelength_nm,
    polarization: cfg.polarization,
    w_min_um: parseFloat(document.getElementById('sw-wmin').value) || 0.5,
    w_max_um: parseFloat(document.getElementById('sw-wmax').value) || 2.0,
    num_points: 7
  };
  document.getElementById('width-cutoff-badge').textContent = 'Sweeping widths...';
  const r = await fetch('/api/sweep_width', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (!data.error) drawWidthSweepPlot(data);
}

function drawWidthSweepPlot(sw) {
  document.getElementById('width-cutoff-badge').textContent = `SM Max W = ${sw.single_mode_max_width_um} um`;
  const series = [
    { x: sw.widths_um, y: sw.neff_fundamental, color: '#38bdf8', dots: true, label: 'n_eff (Fund.)' },
    { x: sw.widths_um, y: sw.ng_fundamental, color: '#34d399', dots: true, label: 'n_g (Group)' }
  ];
  if (sw.neff_higher_order.some(v => v !== null)) {
    series.push({ x: sw.widths_um, y: sw.neff_higher_order, color: '#f87171', dashed: true, dots: true, label: 'TE1/TM1 Cutoff' });
  }
  drawLinePlot('cv-width-sweep', series, 'Waveguide Bottom Width W [um]', 'Effective / Group Index', sw.single_mode_max_width_um);
}

// ==================== TAB 4: LAB SPECTRUM CMT FITTER ====================
async function loadDemoSpectrum(kind) {
  const r = await fetch(`/api/demo_spectrum?kind=${kind}`);
  labSpectrumData = await r.json();
  document.getElementById('fit-lrt').value = labSpectrumData.ring_length_um || 250;
  if (kind === 'multi_fsr') document.getElementById('fit-model').value = 'multi_fsr';
  else document.getElementById('fit-model').value = 'auto';
  await runCmtFitUI();
}

function loadLabCsvFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async () => {
    const lines = reader.result.split(/\r?\n/);
    const wl = [], tr = [];
    for (const ln of lines) {
      const parts = ln.trim().split(/[,\s;]+/);
      if (parts.length >= 2) {
        const x = parseFloat(parts[0]), y = parseFloat(parts[1]);
        if (Number.isFinite(x) && Number.isFinite(y)) { wl.push(x); tr.push(y); }
      }
    }
    if (wl.length > 10) {
      labSpectrumData = { wavelength_nm: wl, transmission: tr };
      await runCmtFitUI();
    }
  };
  reader.readAsText(file);
}

async function runCmtFitUI() {
  if (!labSpectrumData) await loadDemoSpectrum('split_doublet');
  const payload = {
    wavelength_nm: labSpectrumData.wavelength_nm,
    transmission: labSpectrumData.transmission,
    model_type: document.getElementById('fit-model').value,
    known_regime: document.getElementById('fit-regime').value,
    ring_length_um: parseFloat(document.getElementById('fit-lrt').value) || 250
  };
  const r = await fetch('/api/fit_spectrum', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (data.error) return;
  const box = document.getElementById('fit-results-box');
  if (data.mode === 'multi_fsr') {
    const res = data.result;
    box.innerHTML = `<strong>Multi-FSR Group Index Fit</strong><br/>FSR = ${res.mean_fsr_ghz.toFixed(2)} GHz (${res.mean_fsr_nm.toFixed(3)} nm)<br/>Extracted n_g = <strong>${res.ng_extracted.toFixed(4)}</strong><br/>Mean Q_loaded = ${Math.round(res.mean_Q_loaded).toLocaleString()}`;
    drawLinePlot('cv-fit', [{ x: labSpectrumData.wavelength_nm, y: labSpectrumData.transmission, color: '#38bdf8', label: 'Measured Broadband' }], 'Wavelength [nm]', 'Normalized Transmission');
  } else {
    const s = data.summary;
    box.innerHTML = `<strong>Selected Model</strong>: ${s.model_type} (R² = ${s.r_squared.toFixed(5)})<br/>
      lambda_0 = ${s.lambda0_nm.toFixed(5)} nm<br/>
      Q_loaded = <strong>${Math.round(s.Q_loaded).toLocaleString()}</strong> | Q_int = <strong>${Math.round(s.Q_int).toLocaleString()}</strong> | Q_ext = ${Math.round(s.Q_ext).toLocaleString()}<br/>
      Doublet Split 2g/2pi = ${(2 * (s.mu_split_ghz || 0)).toFixed(3)} GHz`;
    drawLinePlot('cv-fit', [
      { x: labSpectrumData.wavelength_nm, y: labSpectrumData.transmission, color: '#64748b', label: 'Measured Data' },
      { x: labSpectrumData.wavelength_nm, y: data.y_fit, color: '#fb923c', width: 2.0, label: 'Analytical CMT Fit' }
    ], 'Wavelength [nm]', 'Normalized Transmission');
  }
}

// ==================== TAB 5: MATERIALS & HARDWARE ====================
async function loadMaterialCurve() {
  const key = document.getElementById('mat-browser-sel').value || '4H-SiC';
  const r = await fetch(`/api/material_dispersion?key=${encodeURIComponent(key)}`);
  const d = await r.json();
  if (d.error) return;
  const series = [{ x: d.wavelength_nm, y: d.nx, color: '#38bdf8', label: 'n_x (In-plane / TE)' }];
  if (d.is_anisotropic) series.push({ x: d.wavelength_nm, y: d.ny, color: '#fb923c', dashed: true, label: 'n_y (Vertical / TM)' });
  drawLinePlot('cv-mat', series, 'Wavelength [nm]', 'Refractive Index n(lambda)');
  document.getElementById('mat-props-text').innerHTML =
    `dn/dT = ${d.dn_dt_per_k.toExponential(2)} /K | r_33 = ${d.r33_pm_per_v} pm/V | n_2 = ${d.n2_m2_per_w.toExponential(2)} m²/W<br/>Source: ${d.source}`;
}

async function runBenchmarkUI() {
  const r = await fetch('/api/benchmark');
  const b = await r.json();
  document.getElementById('hw-detail-box').innerHTML += `<div style="color:#34d399;margin-top:6px;">⚡ 100,000-pt FP64 TMM Spectrum solved in <strong>${b.elapsed_ms.toFixed(2)} ms</strong> (${b.throughput_mpts_per_s.toFixed(2)} M pts/s on ${b.backend_used})</div>`;
}

function exportSpectrumCSV() {
  if (!lastMrrResult) return;
  const sp = lastMrrResult.spectrum;
  let rows = ['wavelength_nm,thru_transmission_dB,drop_transmission_dB'];
  for (let i = 0; i < sp.wavelength_nm.length; i++) {
    rows.push(`${sp.wavelength_nm[i]},${sp.thru_dB[i]},${sp.drop_dB ? sp.drop_dB[i] : ''}`);
  }
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'openmrr_spectrum.csv';
  a.click();
}

// ==================== BOOTSTRAP ====================
(async function boot() {
  const [hwRes, matRes] = await Promise.all([fetch('/api/hardware'), fetch('/api/materials')]);
  const hw = await hwRes.json();
  const matData = await matRes.json();

  document.getElementById('hw-badge').textContent = `${hw.recommended_backend}`;
  document.getElementById('hw-detail-box').innerHTML = `
    <div><strong>OS / Arch</strong>: ${hw.os_name} (${hw.arch})</div>
    <div><strong>CPU</strong>: ${hw.cpu_brand} (${hw.cpu_cores} cores)</div>
    <div><strong>GPU / Accelerator</strong>: ${hw.gpu_name || 'CPU Vectorized'}</div>
    <div><strong>Selected Engine</strong>: <span style="color:#38bdf8;">${hw.recommended_backend}</span></div>`;

  catalogMaterials = matData.materials;
  catalogTopologies = matData.topologies;

  const selTop = document.getElementById('cfg-topology');
  Object.entries(catalogTopologies).forEach(([k, v]) => {
    const o = document.createElement('option'); o.value = k; o.textContent = v.name; selTop.appendChild(o);
  });

  ['cfg-material', 'mat-browser-sel'].forEach(id => {
    const el = document.getElementById(id);
    catalogMaterials.forEach(m => {
      if (id === 'cfg-material' && (m.key === 'Air' || m.key === 'SiO2')) return;
      const o = document.createElement('option'); o.value = m.key; o.textContent = `${m.key} — ${m.name}`; el.appendChild(o);
    });
  });
  document.getElementById('mat-browser-sel').value = '4H-SiC';

  await initChat();
  loadMaterialCurve();
})();
</script>
</body>
</html>
"""
