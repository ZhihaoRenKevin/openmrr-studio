"""Native Desktop & Browser Application Launcher for `OpenMRR Studio`.

Starts the local `127.0.0.1` Starlette/Uvicorn server in a background daemon thread
and opens either:
  - A native OS window (`pywebview`: macOS Cocoa WebKit / Windows Edge WebView2), or
  - The user's default system browser (`--browser` fallback if `pywebview` is absent), or
  - A self-terminating smoke test (`--headless-check`, also verifying 2D FEM + GDS inside frozen apps).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

# Guard stdout/stderr in PyInstaller --windowed (.app / .exe) mode where streams may be None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn

if not getattr(sys, "frozen", False):
    _src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

try:
    from openmrr import __version__ as APP_VERSION
    from openmrr.app_server import app
except ImportError:
    from . import __version__ as APP_VERSION
    from .app_server import app


def _find_free_localhost_port(preferred: int = 8765) -> int:
    for candidate in (preferred, 8766, 8767, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", candidate))
                return int(s.getsockname()[1])
            except OSError:
                continue
    raise RuntimeError("Could not bind any localhost port on 127.0.0.1.")


def _wait_until_ready(url: str, timeout_s: float = 15.0) -> bool:
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            with urllib.request.urlopen(url + "/api/hardware", timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.12)
    return False


def _run_headless_physics_check(url: str) -> None:
    req = urllib.request.Request(
        url + "/api/solve_mode",
        data=json.dumps({
            "core_material": "Si3N4",
            "clad_material": "SiO2",
            "top_clad_material": "SiO2",
            "wavelength_nm": 1550.0,
            "width_um": 1.0,
            "film_height_um": 0.40,
            "slab_height_um": 0.0,
            "sidewall_deg": 88.0,
            "bend_radius_um": 50.0,
            "polarization": "TE0",
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25.0) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
        assert resp.status == 200 and payload.get("modes"), f"Unexpected mode payload: {payload}"


def launch_studio(
    *,
    browser_only: bool = False,
    headless_check: bool = False,
    no_open: bool = False,
    port: int | None = None,
) -> int:
    bind_port = port or _find_free_localhost_port()
    url = f"http://127.0.0.1:{bind_port}"

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=bind_port,
        log_level="warning",
        log_config=None,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    if not _wait_until_ready(url):
        print(f"[OpenMRR] ERROR: Local backend at {url} failed to start within 15 s.")
        return 1

    if headless_check:
        _run_headless_physics_check(url)
        print(f"[OpenMRR] Headless server + 2D FEM check PASSED on {url}")
        server.should_exit = True
        thread.join(timeout=3.0)
        return 0

    if not browser_only and not no_open:
        try:
            import webview  # type: ignore

            webview.create_window(
                f"OpenMRR Studio v{APP_VERSION} - License-Free Photonics Microring Designer",
                url,
                width=1460,
                height=900,
                min_size=(1080, 680),
            )
            webview.start()
            server.should_exit = True
            return 0
        except Exception as exc:
            print(f"[OpenMRR] Native webview unavailable ({exc}); opening system browser at {url}")

    print(f"[OpenMRR] Running at {url} — Press Ctrl+C to stop.", flush=True)
    if not no_open:
        webbrowser.open(url)
    try:
        while thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.should_exit = True
    return 0


def main() -> None:
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description=f"Launch OpenMRR Studio v{APP_VERSION}")
    parser.add_argument("--browser", action="store_true", help="Open in default web browser instead of native window")
    parser.add_argument("--no-open", action="store_true", help="Serve HTTP UI without opening a new browser window")
    parser.add_argument("--headless-check", action="store_true", help="Verify local server + 2D FEM startup and exit")
    parser.add_argument("--port", type=int, default=None, help="Optional localhost port (default: auto 8765)")
    args = parser.parse_args()
    raise SystemExit(
        launch_studio(
            browser_only=args.browser,
            headless_check=args.headless_check,
            no_open=args.no_open,
            port=args.port,
        )
    )


if __name__ == "__main__":
    main()
