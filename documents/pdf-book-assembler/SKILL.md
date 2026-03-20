---
name: pdf-book-assembler
description: Assemble book-style PDFs from one or more source PDFs using CLI PDF tools. Use when Codex needs to collate PDFs in a specific order, drop repeated cover/JSTOR pages, add chapter/section bookmarks, rotate landscape pages to portrait, or optionally crop shared whitespace proportionally across pages.
---

# PDF Book Assembler

## Overview

Build book-like PDFs with a command-line-first pipeline. This skill uses `pdfseparate`, `pdfunite`, `gs`, `pdfinfo`, and optionally `pdftoppm` for the PDF work; the bundled script only orchestrates those tools and computes crop margins.

## Use The Workflow

1. Inspect the source PDFs with `find`, `pdfinfo`, and, when needed, `pdftotext -layout`.
2. Determine the exact source order and any `drop_first_page`, `start_page`, or `end_page` rules.
3. Derive bookmark targets as output PDF pages after those page-selection rules are applied.
4. Write a JSON spec and run `scripts/build_pdf_book.py <spec.json>`.
5. Check the JSON summary, then verify page count and outline structure on the output PDF.

## Build The Spec

Read [references/spec.md](references/spec.md) for the JSON shape and examples.

Use `level: 1` for chapters and other top-level entries. Use `level: 2` for sections under the immediately preceding level-1 bookmark. Do not skip levels.

Enable `normalize_portrait` when mixed-orientation pages should all read upright in portrait view.

Enable `crop_whitespace` only when the page set has consistent margins. The script computes one common proportional crop across the nonblank pages; it is intentionally conservative.

## Run The Script

From the skill directory:

```bash
python3 scripts/build_pdf_book.py /path/to/spec.json
```

The script prints a JSON summary with:
- `pages`
- `rotated_pages`
- `crop_margins`
- `bookmark_count`
- `page_map`

Use `page_map` to confirm the merge order and the output-page offsets.

## Validate The Output

Check page count with:

```bash
pdfinfo /path/to/output.pdf
```

If bookmarks were added, spot-check the outline with a PDF viewer. For automated debugging or forward-testing, it is acceptable to inspect the resulting outline with local tooling after the CLI pipeline finishes.

## Constraints

Prefer this skill when the job is fundamentally page-level PDF assembly and cleanup.

Do not use this skill for form filling, OCR, or fine-grained PDF object editing that requires a library-level PDF editor.
