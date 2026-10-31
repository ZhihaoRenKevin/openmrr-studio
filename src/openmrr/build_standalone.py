"""Cross-Platform Standalone App Builder (`macOS .app` & `Windows .exe` CPU/CUDA).

Packages `OpenMRR Studio v3.0` via PyInstaller with zero GPL dependencies:
  python -m openmrr.build_standalone --target macos
  python -m openmrr.build_standalone --target windows-cpu
  python -m openmrr.build_standalone --target windows-cuda
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def build_package(target: str) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    entry = repo_root / "src" / "openmrr" / "desktop_app.py"
    name = {
        "macos": "OpenMRR-Studio-macOS-AppleSilicon",
        "windows-cpu": "OpenMRR-Studio-Win64-CPU",
        "windows-cuda": "OpenMRR-Studio-Win64-CUDA",
    }[target]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        name,
        "--paths",
        str(repo_root / "src"),
        "--hidden-import=scipy.sparse.linalg._eigen.arpack",
        "--hidden-import=skfem",
        "--hidden-import=gdstk",
        str(entry),
    ]
    if target == "windows-cpu":
        cmd.extend(["--exclude-module", "torch", "--exclude-module", "cupy"])

    print("[OpenMRR Builder] Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(repo_root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build standalone OpenMRR Studio desktop bundle")
    parser.add_argument("--target", choices=["macos", "windows-cpu", "windows-cuda"], required=True)
    args = parser.parse_args()
    raise SystemExit(build_package(args.target))


if __name__ == "__main__":
    main()
