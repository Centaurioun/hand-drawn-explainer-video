#!/usr/bin/env python3
"""
Streaming stroke animation - environment bootstrap script

Responsibilities:
  1. Create an isolated Python virtual environment under the skill directory (reuse it if present)
  2. Check whether required third-party libraries can be imported
  3. Automatically install missing libraries
  4. Print ENV_PY=<interpreter path> on the final line for callers

Usage:
  python prepare_env.py          # Create environment, install dependencies, and print ENV_PY
  python prepare_env.py --check  # Check only; exit with a nonzero status if anything is missing
"""
from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

# Skill root directory: two levels above this script
SKILL_ROOT = Path(__file__).resolve().parent.parent
VENV_ROOT = SKILL_ROOT / ".venv"

# Interpreter import names -> display package names. Installation uses the version constraints file at the repository root.
DEPS: dict[str, str] = {
    "cv2": "opencv-python-headless",
    "numpy": "numpy",
    "av": "av",  # PyAV: pip-installable H.264 encoding without system ffmpeg
    "PIL": "Pillow",  # render_annotation_preview.py draws numbered region previews (including multilingual labels)
}


def interpreter_path() -> Path:
    """Return the virtual environment's Python executable path (cross-platform)."""
    if sys.platform.startswith("win"):
        return VENV_ROOT / "Scripts" / "python.exe"
    return VENV_ROOT / "bin" / "python"


def ensure_venv(check_only: bool) -> Path:
    py = interpreter_path()
    if VENV_ROOT.exists() and py.exists():
        print(f"[ok] Reusing existing virtual environment: {VENV_ROOT}")
        return py

    if check_only:
        print(f"[err] Virtual environment has not been created: {VENV_ROOT}")
        sys.exit(1)

    print(f"[..] Creating virtual environment: {VENV_ROOT}")
    venv.create(str(VENV_ROOT), with_pip=True)
    print("[ok] Virtual environment ready")
    return py


def can_import(py: Path, import_name: str) -> bool:
    probe = subprocess.run(
        [str(py), "-c", f"import {import_name}"],
        capture_output=True,
    )
    return probe.returncode == 0


def install(py: Path, packages: list[str]) -> bool:
    if not packages:
        return True
    print(f"[..] Installing dependencies: {', '.join(packages)}")
    requirements = SKILL_ROOT.parent.parent / "requirements-media.txt"
    install_args = ["-r", str(requirements)] if requirements.is_file() else packages
    res = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", *install_args],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"[err] Installation failed:\n{res.stderr}")
        print("[hint] Check the Python version, proxy, certificates, and package index. You can also install requirements-media.txt manually and retry --check.")
        return False
    print("[ok] Dependency installation complete")
    return True


def main() -> None:
    check_only = "--check" in sys.argv

    py = ensure_venv(check_only)

    missing: list[str] = []
    for import_name, pip_name in DEPS.items():
        if can_import(py, import_name):
            print(f"[ok] {pip_name}")
        else:
            print(f"[miss] {pip_name}")
            missing.append(pip_name)

    if missing:
        if check_only:
            print(f"\nMissing {len(missing)} dependencies: {', '.join(missing)}")
            sys.exit(1)
        if not install(py, missing):
            sys.exit(1)

    # Final line: conventional output for callers
    print(f"\nENV_PY={py}")


if __name__ == "__main__":
    main()
