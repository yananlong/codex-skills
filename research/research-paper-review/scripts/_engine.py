#!/usr/bin/env python3
"""Helpers for managing the upstream OpenAIReview engine."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_URL = "https://github.com/ChicagoHAI/OpenAIReview.git"
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VENV = Path(
    os.environ.get("OPENAIREVIEW_VENV", SKILL_DIR / ".openaireview-venv")
).expanduser()


def _python_path(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


def _run(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess[str]:
    print(f"+ {shlex.join(str(part) for part in cmd)}", file=sys.stderr)
    return subprocess.run(
        [str(part) for part in cmd],
        check=True,
        text=True,
        **kwargs,
    )


def ensure_virtualenv(venv_dir: Path) -> Path:
    venv_dir = venv_dir.expanduser().resolve()
    python_path = _python_path(venv_dir)
    if not python_path.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "venv", str(venv_dir)])
    return venv_dir


def build_install_spec(source: str, ref: str, extras: Sequence[str]) -> str:
    extras_suffix = f"[{','.join(extras)}]" if extras else ""
    if source == "pypi":
        return f"openaireview{extras_suffix}"
    return f"openaireview{extras_suffix} @ git+{REPO_URL}@{ref}"


def install_engine(
    venv_dir: Path,
    source: str = "github",
    ref: str = "main",
    extras: Sequence[str] | None = None,
    upgrade: bool = True,
    reinstall: bool = False,
) -> Path:
    extras = list(dict.fromkeys(extras or []))
    venv_dir = ensure_virtualenv(venv_dir)
    python_path = _python_path(venv_dir)

    pip_bootstrap = [str(python_path), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
    _run(pip_bootstrap)

    install_cmd = [str(python_path), "-m", "pip", "install"]
    if upgrade:
        install_cmd.append("--upgrade")
    if reinstall:
        install_cmd.append("--force-reinstall")
    install_cmd.append(build_install_spec(source=source, ref=ref, extras=extras))
    _run(install_cmd)
    assert_engine_installed(venv_dir)
    return venv_dir


def assert_engine_installed(venv_dir: Path) -> None:
    python_path = _python_path(venv_dir.expanduser().resolve())
    if not python_path.exists():
        raise SystemExit(
            f"OpenAIReview virtualenv not found at {venv_dir}. "
            "Run `python3 scripts/install_engine.py` first."
        )
    probe = subprocess.run(
        [str(python_path), "-c", "import reviewer"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise SystemExit(
            "OpenAIReview is not installed in the configured virtualenv. "
            "Run `python3 scripts/install_engine.py` first."
        )


def _query_package_path(venv_dir: Path, expression: str) -> Path:
    python_path = _python_path(venv_dir.expanduser().resolve())
    result = subprocess.run(
        [
            str(python_path),
            "-c",
            (
                "from pathlib import Path; "
                "import reviewer; "
                f"print(Path({expression}).resolve())"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def package_dir(venv_dir: Path) -> Path:
    assert_engine_installed(venv_dir)
    return _query_package_path(venv_dir, "reviewer.__file__").parent


def packaged_skill_dir(venv_dir: Path) -> Path:
    return package_dir(venv_dir) / "skill"


def run_cli(venv_dir: Path, cli_args: Sequence[str]) -> int:
    assert_engine_installed(venv_dir)
    python_path = _python_path(venv_dir.expanduser().resolve())
    proc = subprocess.run([str(python_path), "-m", "reviewer.cli", *cli_args], check=False)
    return proc.returncode


def run_packaged_skill_script(venv_dir: Path, relative_script: str, script_args: Sequence[str]) -> int:
    assert_engine_installed(venv_dir)
    python_path = _python_path(venv_dir.expanduser().resolve())
    script_path = packaged_skill_dir(venv_dir) / relative_script
    if not script_path.exists():
        raise SystemExit(f"Packaged skill script not found: {script_path}")
    proc = subprocess.run([str(python_path), str(script_path), *script_args], check=False)
    return proc.returncode
