#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


REQUIRED_TOOLS = ["pdfinfo", "pdfseparate", "pdfunite", "gs"]
OPTIONAL_TOOLS = {"crop": ["pdftoppm"]}


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def which(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        fail(f"Required tool not found in PATH: {tool}")
    return path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def load_spec(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Spec file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in spec file {path}: {exc}")
    require(isinstance(data, dict), "Spec root must be a JSON object.")
    return data


def resolve_path(spec_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (spec_path.parent / candidate).resolve()


def pdfinfo_text(path: Path) -> str:
    result = run([which("pdfinfo"), str(path)])
    return "\n".join(part for part in [result.stdout, result.stderr] if part)


def page_count(path: Path) -> int:
    for line in pdfinfo_text(path).splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    fail(f"Could not read page count for {path}")


def page_size_points(path: Path) -> tuple[float, float]:
    for line in pdfinfo_text(path).splitlines():
        if line.startswith("Page size:"):
            payload = line.split(":", 1)[1].strip()
            dims = payload.split("pts", 1)[0].strip()
            width_str, height_str = [part.strip() for part in dims.split("x", 1)]
            return float(width_str), float(height_str)
    fail(f"Could not read page size for {path}")


def selected_page_bounds(total_pages: int, item: dict[str, Any]) -> tuple[int, int]:
    start_page = int(item.get("start_page", 1))
    end_page = int(item.get("end_page", total_pages))
    if item.get("drop_first_page", False):
        start_page += 1
    require(start_page >= 1, f"start_page must be >= 1 for {item['path']}")
    require(end_page >= start_page, f"end_page must be >= start_page for {item['path']}")
    require(end_page <= total_pages, f"end_page exceeds page count for {item['path']}")
    return start_page, end_page


def escape_ps_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def extract_pages(
    source_pdf: Path,
    start_page: int,
    end_page: int,
    temp_dir: Path,
    prefix: str,
) -> list[Path]:
    pattern = temp_dir / f"{prefix}-%04d.pdf"
    run(
        [
            which("pdfseparate"),
            "-f",
            str(start_page),
            "-l",
            str(end_page),
            str(source_pdf),
            str(pattern),
        ]
    )
    page_files = sorted(temp_dir.glob(f"{prefix}-*.pdf"))
    require(
        len(page_files) == (end_page - start_page + 1),
        f"Expected {end_page - start_page + 1} extracted pages from {source_pdf}, got {len(page_files)}.",
    )
    return page_files


def rotate_page_to_portrait(page_pdf: Path) -> bool:
    width, height = page_size_points(page_pdf)
    if width <= height:
        return False
    rotated_pdf = page_pdf.with_name(f"{page_pdf.stem}.rotated.pdf")
    run(
        [
            which("gs"),
            "-q",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={rotated_pdf}",
            "-c",
            "<</Orientation 3>> setpagedevice",
            "-f",
            str(page_pdf),
        ]
    )
    rotated_pdf.replace(page_pdf)
    return True


def render_page_png(page_pdf: Path, png_base: Path, dpi: int) -> Path:
    run(
        [
            which("pdftoppm"),
            "-png",
            "-singlefile",
            "-r",
            str(dpi),
            str(page_pdf),
            str(png_base),
        ]
    )
    return png_base.with_suffix(".png")


def image_margin_ratios(image_path: Path, threshold: int) -> dict[str, float] | None:
    image = Image.open(image_path).convert("L")
    array = np.asarray(image)
    mask = array < threshold
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    height, width = array.shape
    return {
        "left": float(xs.min()) / float(width),
        "right": float(width - (xs.max() + 1)) / float(width),
        "top": float(ys.min()) / float(height),
        "bottom": float(height - (ys.max() + 1)) / float(height),
    }


def compute_common_crop_ratios(
    page_files: list[Path],
    crop_spec: dict[str, Any],
    temp_dir: Path,
) -> dict[str, float]:
    require(shutil.which("pdftoppm") is not None, "pdftoppm is required when crop_whitespace is enabled.")
    dpi = int(crop_spec.get("render_dpi", 96))
    threshold = int(crop_spec.get("threshold", 245))
    padding_ratio = float(crop_spec.get("padding_ratio", 0.01))
    require(dpi > 0, "crop_whitespace.render_dpi must be > 0.")
    require(0 <= threshold <= 255, "crop_whitespace.threshold must be between 0 and 255.")
    require(0 <= padding_ratio < 0.25, "crop_whitespace.padding_ratio must be between 0 and 0.25.")

    rendered_dir = temp_dir / "rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    margins = []
    for index, page_pdf in enumerate(page_files, start=1):
        png_base = rendered_dir / f"page-{index:04d}"
        image_path = render_page_png(page_pdf, png_base, dpi)
        margins.append(image_margin_ratios(image_path, threshold))

    nonblank = [margin for margin in margins if margin is not None]
    if not nonblank:
        return {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0}

    return {
        side: max(0.0, min(margin[side] for margin in nonblank) - padding_ratio)
        for side in ("left", "right", "top", "bottom")
    }


def crop_page(page_pdf: Path, margins: dict[str, float]) -> None:
    width, height = page_size_points(page_pdf)
    left = width * margins["left"]
    right = width - (width * margins["right"])
    bottom = height * margins["bottom"]
    top = height - (height * margins["top"])
    cropped_pdf = page_pdf.with_name(f"{page_pdf.stem}.cropped.pdf")
    pdfmark = (
        f"[/CropBox [{left:.3f} {bottom:.3f} {right:.3f} {top:.3f}] /PAGES pdfmark "
        f"[/TrimBox [{left:.3f} {bottom:.3f} {right:.3f} {top:.3f}] /PAGES pdfmark"
    )
    run(
        [
            which("gs"),
            "-q",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={cropped_pdf}",
            "-c",
            pdfmark,
            "-f",
            str(page_pdf),
        ]
    )
    cropped_pdf.replace(page_pdf)


def merge_pages(page_files: list[Path], output_pdf: Path) -> None:
    require(page_files, "No pages were selected for merge.")
    run([which("pdfunite"), *[str(path) for path in page_files], str(output_pdf)])


def descendant_count(bookmarks: list[dict[str, Any]], index: int) -> int:
    level = int(bookmarks[index].get("level", 1))
    count = 0
    for later in bookmarks[index + 1 :]:
        later_level = int(later.get("level", 1))
        if later_level <= level:
            break
        count += 1
    return count


def build_pdfmark_text(bookmarks: list[dict[str, Any]]) -> str:
    if not bookmarks:
        return ""
    parents_seen: set[int] = set()
    lines = ["[{Catalog} <</PageMode /UseOutlines>> /PUT pdfmark"]
    for index, bookmark in enumerate(bookmarks):
        require(isinstance(bookmark, dict), "Each bookmarks entry must be an object.")
        title = str(bookmark["title"])
        page = int(bookmark["page"])
        level = int(bookmark.get("level", 1))
        require(level >= 1, f"Bookmark level must be >= 1 for {title}")
        if level > 1:
            require(level - 1 in parents_seen, f"Bookmark level jumps too far at {title}")
        parent_count = descendant_count(bookmarks, index)
        count_part = f"/Count {parent_count} " if parent_count else ""
        lines.append(
            f"[ {count_part}/Title ({escape_ps_string(title)}) /Page {page} /View [/Fit] /OUT pdfmark"
        )
        parents_seen.add(level)
        for stale_level in [seen for seen in parents_seen if seen > level]:
            parents_seen.remove(stale_level)
    return "\n".join(lines) + "\n"


def add_bookmarks(input_pdf: Path, output_pdf: Path, bookmarks: list[dict[str, Any]], temp_dir: Path) -> None:
    pdfmark_path = temp_dir / "bookmarks.ps"
    pdfmark_path.write_text(build_pdfmark_text(bookmarks), encoding="utf-8")
    run(
        [
            which("gs"),
            "-q",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={output_pdf}",
            str(pdfmark_path),
            str(input_pdf),
        ]
    )


def validate_bookmark_spec(bookmarks: list[dict[str, Any]], total_pages: int) -> None:
    for bookmark in bookmarks:
        page = int(bookmark["page"])
        require(1 <= page <= total_pages, f"Bookmark page is out of range: {bookmark['title']} -> {page}")


def ensure_tools_for_spec(spec: dict[str, Any]) -> None:
    for tool in REQUIRED_TOOLS:
        which(tool)
    if spec.get("crop_whitespace", False):
        for tool in OPTIONAL_TOOLS["crop"]:
            which(tool)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a book-style PDF from a JSON spec using CLI PDF tools.")
    parser.add_argument("spec", help="Path to a JSON spec file.")
    args = parser.parse_args()

    spec_path = Path(args.spec).expanduser().resolve()
    spec = load_spec(spec_path)
    ensure_tools_for_spec(spec)

    output_path = resolve_path(spec_path, str(spec["output"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    inputs = spec.get("inputs")
    require(isinstance(inputs, list) and inputs, "Spec must include a non-empty inputs array.")

    with tempfile.TemporaryDirectory(prefix="pdf-book-cli-") as temp_name:
        temp_dir = Path(temp_name)
        pages_dir = temp_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        page_files: list[Path] = []
        page_map: list[dict[str, Any]] = []
        rotated_pages = 0

        for index, item in enumerate(inputs, start=1):
            require(isinstance(item, dict), "Each inputs entry must be an object.")
            require("path" in item, "Each inputs entry must include path.")
            source_path = resolve_path(spec_path, str(item["path"]))
            require(source_path.exists(), f"Input PDF not found: {source_path}")
            total_pages = page_count(source_path)
            start_page, end_page = selected_page_bounds(total_pages, item)
            extracted = extract_pages(source_path, start_page, end_page, pages_dir, f"{index:04d}")
            output_start = len(page_files) + 1
            for page_pdf in extracted:
                if spec.get("normalize_portrait", False):
                    rotated_pages += int(rotate_page_to_portrait(page_pdf))
                page_files.append(page_pdf)
            output_end = len(page_files)
            page_map.append(
                {
                    "path": str(source_path),
                    "input_start_page": start_page,
                    "input_end_page": end_page,
                    "output_start_page": output_start,
                    "output_end_page": output_end,
                }
            )

        crop_margins = None
        crop_spec = spec.get("crop_whitespace", False)
        if crop_spec:
            if crop_spec is True:
                crop_spec = {}
            require(isinstance(crop_spec, dict), "crop_whitespace must be false, true, or an object.")
            crop_margins = compute_common_crop_ratios(page_files, crop_spec, temp_dir)
            for page_pdf in page_files:
                crop_page(page_pdf, crop_margins)

        merged_pdf = temp_dir / "merged.pdf"
        merge_pages(page_files, merged_pdf)

        bookmarks = spec.get("bookmarks", [])
        require(isinstance(bookmarks, list), "bookmarks must be an array when provided.")
        validate_bookmark_spec(bookmarks, len(page_files))

        if bookmarks:
            add_bookmarks(merged_pdf, output_path, bookmarks, temp_dir)
        else:
            shutil.copyfile(merged_pdf, output_path)

    summary = {
        "output": str(output_path),
        "pages": len(page_files),
        "rotated_pages": rotated_pages,
        "crop_margins": crop_margins,
        "bookmark_count": len(bookmarks),
        "page_map": page_map,
    }
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
