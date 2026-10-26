#!/usr/bin/env python3
"""Helpers for managing the upstream OpenAIReview engine.

The engine is pinned: ENGINE_VERSION on PyPI, ENGINE_COMMIT (the matching release tag) on GitHub.
It installs into a versioned virtualenv outside the skill directory, so packaging or updating the
skill never carries or clobbers it. OPENAIREVIEW_VENV overrides the location.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_URL = "https://github.com/ChicagoHAI/OpenAIReview.git"
ENGINE_VERSION = "0.3.0"
ENGINE_TAG = "v0.3.0"
ENGINE_COMMIT = "27740f8434cf18bd2d66d228291d9dcc3e046bc2"
ENGINE_MIN_PYTHON = (3, 12)
MARKER = "codex-skills-engine.json"
SKILL_DIR = Path(__file__).resolve().parent.parent
LEGACY_VENV = SKILL_DIR / ".openaireview-venv"


def default_venv() -> Path:
    if os.environ.get("OPENAIREVIEW_VENV"):
        return Path(os.environ["OPENAIREVIEW_VENV"]).expanduser()
    data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share").expanduser()
    return data_home / "codex-skills" / f"openaireview-{ENGINE_VERSION}"


DEFAULT_VENV = default_venv()


def is_pinned(source: str, ref: str) -> bool:
    return source == "pypi" or ref in (ENGINE_COMMIT, ENGINE_TAG)


def pin_problem(installed_version: str | None, marker: dict | None) -> str | None:
    """Why an installed engine does not satisfy the pin, or None when it does.

    An install made with an explicit other ref records pinned=false in its marker and is accepted,
    so a deliberate override keeps working; anything else must match ENGINE_VERSION.
    """
    if marker and marker.get("pinned") is False:
        return None
    if installed_version != ENGINE_VERSION:
        return (
            f"OpenAIReview {installed_version or 'of unknown version'} is installed, but this skill is pinned "
            f"to {ENGINE_VERSION} ({ENGINE_TAG}, {ENGINE_COMMIT[:12]}). Run `python3 scripts/install_engine.py "
            "--reinstall`."
        )
    return None


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
    if sys.version_info[:2] < ENGINE_MIN_PYTHON:
        raise SystemExit(
            f"OpenAIReview {ENGINE_VERSION} needs Python {'.'.join(map(str, ENGINE_MIN_PYTHON))} or newer; "
            f"this is {sys.version.split()[0]}. Run install_engine.py with a newer python3."
        )
    venv_dir = venv_dir.expanduser().resolve()
    try:
        venv_dir.relative_to(SKILL_DIR)
    except ValueError:
        pass
    else:
        raise SystemExit(f"install the engine outside the skill directory, not in {venv_dir}")
    python_path = _python_path(venv_dir)
    if not python_path.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "venv", str(venv_dir)])
    return venv_dir


def build_install_spec(source: str, ref: str, extras: Sequence[str]) -> str:
    extras_suffix = f"[{','.join(extras)}]" if extras else ""
    if source == "pypi":
        return f"openaireview{extras_suffix}=={ENGINE_VERSION}"
    return f"openaireview{extras_suffix} @ git+{REPO_URL}@{ref}"


def install_engine(
    venv_dir: Path,
    source: str = "github",
    ref: str = ENGINE_COMMIT,
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
    pinned = is_pinned(source, ref)
    if not pinned:
        print(f"warning: installing unpinned ref {ref}; the pinned engine is {ENGINE_TAG} ({ENGINE_COMMIT[:12]})", file=sys.stderr)
    _run(install_cmd)
    marker = {"version": ENGINE_VERSION, "source": source, "ref": ref if source == "github" else ENGINE_VERSION, "pinned": pinned}
    (venv_dir / MARKER).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    assert_engine_installed(venv_dir)
    return venv_dir


def installed_version(venv_dir: Path) -> str | None:
    python_path = _python_path(venv_dir.expanduser().resolve())
    probe = subprocess.run(
        [str(python_path), "-c", "import importlib.metadata as m; print(m.version('openaireview'))"],
        capture_output=True,
        text=True,
    )
    return probe.stdout.strip() if probe.returncode == 0 else None


def read_marker(venv_dir: Path) -> dict | None:
    try:
        return json.loads((venv_dir.expanduser().resolve() / MARKER).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def assert_engine_installed(venv_dir: Path) -> None:
    python_path = _python_path(venv_dir.expanduser().resolve())
    if not python_path.exists():
        legacy = (
            f" An older unpinned install exists inside the skill at {LEGACY_VENV}; it is no longer used and "
            "can be deleted."
            if (LEGACY_VENV / "bin" / "python").exists()
            else ""
        )
        raise SystemExit(
            f"OpenAIReview virtualenv not found at {venv_dir}. "
            "Run `python3 scripts/install_engine.py` first." + legacy
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
    problem = pin_problem(installed_version(venv_dir), read_marker(venv_dir))
    if problem:
        raise SystemExit(problem)


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
