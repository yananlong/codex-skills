from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _as_source_lines(text: str) -> list[str]:
    if not text:
        return []
    return text.splitlines(True)


def md_cell(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": metadata or {}, "source": _as_source_lines(text)}


def code_cell(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "metadata": metadata or {},
        "execution_count": None,
        "outputs": [],
        "source": _as_source_lines(text),
    }


def new_notebook(
    cells: list[dict[str, Any]],
    *,
    kernel_name: str = "python3",
    kernel_display_name: str = "Python 3",
    language: str = "python",
) -> dict[str, Any]:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"name": kernel_name, "display_name": kernel_display_name, "language": language},
            "language_info": {"name": language},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(path: str | Path, notebook: dict[str, Any]) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out_path

