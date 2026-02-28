#!/usr/bin/env python3
from __future__ import annotations

import argparse

from ipynb_json import code_cell, md_cell, new_notebook, write_notebook


_PY_LANGS = {"py", "python", "ipython"}
_BASH_LANGS = {"bash", "sh", "shell"}


def _is_code_fence(lang: str, *, bare_fence_as_code: bool) -> bool:
    normalized = (lang or "").strip().lower()
    if normalized in _PY_LANGS or normalized in _BASH_LANGS:
        return True
    if normalized == "" and bare_fence_as_code:
        return True
    return False


def _scaffold_preamble(*, title: str | None) -> list[dict]:
    cells: list[dict] = []
    if title:
        cells.append(md_cell(f"# {title}\n"))
    cells.append(md_cell("## Goal\n\nState what this notebook should demonstrate/produce.\n"))
    cells.append(
        md_cell(
            "## Setup\n\n"
            "- Keep the notebook runnable top-to-bottom.\n"
            "- Prefer minimal dependencies; document any non-stdlib deps.\n"
        )
    )
    cells.append(
        code_cell(
            "import platform\n"
            "import random\n"
            "import sys\n"
            "\n"
            "print(\"Python:\", sys.version)\n"
            "print(\"Platform:\", platform.platform())\n"
            "\n"
            "SEED = 0\n"
            "random.seed(SEED)\n"
            "\n"
            "try:\n"
            "    import numpy as np  # type: ignore\n"
            "\n"
            "    np.random.seed(SEED)\n"
            "except Exception:\n"
            "    np = None\n"
        )
    )
    cells.append(md_cell("## Source notes\n\nConverted from Markdown. Edit/restructure as needed.\n"))
    return cells


def _scaffold_postamble() -> list[dict]:
    return [
        md_cell("## Validation\n\nAdd sanity checks and a few key invariants as tests.\n"),
        code_cell("# TODO: Replace with real tests.\nassert True\n"),
        md_cell("## Demo / Experiments\n\nShow usage, generate plots/tables, and interpret results.\n"),
    ]


def markdown_to_cells(markdown: str, *, bare_fence_as_code: bool) -> list[dict]:
    cells: list[dict] = []
    markdown_buf: list[str] = []

    state: str = "markdown"  # markdown | raw_fence | code_fence
    fence_lang: str = ""
    code_buf: list[str] = []

    def flush_markdown() -> None:
        nonlocal markdown_buf
        text = "".join(markdown_buf)
        if text.strip():
            cells.append(md_cell(text))
        markdown_buf = []

    for line in markdown.splitlines(True):
        stripped = line.lstrip()
        is_fence = stripped.startswith("```")

        if state == "markdown":
            if is_fence:
                fence_lang = stripped[3:].strip()
                if _is_code_fence(fence_lang, bare_fence_as_code=bare_fence_as_code):
                    flush_markdown()
                    state = "code_fence"
                    code_buf = []
                else:
                    state = "raw_fence"
                    markdown_buf.append(line)
            else:
                markdown_buf.append(line)
            continue

        if state == "raw_fence":
            markdown_buf.append(line)
            if is_fence:
                state = "markdown"
                fence_lang = ""
            continue

        if state == "code_fence":
            if is_fence:
                code = "".join(code_buf)
                lang = (fence_lang or "").strip().lower()
                if lang in _BASH_LANGS:
                    code = "%%bash\n" + code
                cells.append(code_cell(code))
                state = "markdown"
                fence_lang = ""
                code_buf = []
            else:
                code_buf.append(line)
            continue

        raise RuntimeError(f"Unknown state: {state}")

    if state == "code_fence":
        code = "".join(code_buf)
        lang = (fence_lang or "").strip().lower()
        if lang in _BASH_LANGS:
            code = "%%bash\n" + code
        cells.append(code_cell(code))

    flush_markdown()
    return cells


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown into a Jupyter notebook (.ipynb).")
    parser.add_argument("input_md", help="Input Markdown file")
    parser.add_argument("--out", required=True, help="Output .ipynb path")
    parser.add_argument("--title", help="Optional title (adds a top header cell)")
    parser.add_argument(
        "--with-scaffold",
        action="store_true",
        help="Prepend a minimal product-ready scaffold (Goal/Setup) and append Validation/Demo sections",
    )
    parser.add_argument(
        "--bare-fence-as-code",
        action="store_true",
        help="Treat ``` (no language) blocks as Python code cells (default: keep as Markdown code blocks)",
    )
    args = parser.parse_args()

    markdown_text = open(args.input_md, "r", encoding="utf-8").read()
    converted_cells = markdown_to_cells(markdown_text, bare_fence_as_code=args.bare_fence_as_code)

    cells: list[dict] = []
    if args.with_scaffold:
        cells.extend(_scaffold_preamble(title=args.title))
        cells.extend(converted_cells)
        cells.extend(_scaffold_postamble())
    else:
        if args.title:
            cells.append(md_cell(f"# {args.title}\n"))
        cells.extend(converted_cells)

    notebook = new_notebook(cells)
    out_path = write_notebook(args.out, notebook)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()

