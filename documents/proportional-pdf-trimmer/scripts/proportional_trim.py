#!/usr/bin/env python3
"""Trim PDF whitespace to a single aspect-ratio-preserving crop size.

The script detects visible content on every page from a grayscale render, computes
for each page the smallest crop that contains that content while preserving the
page aspect ratio, chooses the largest required crop as the common target size,
and repositions that same-size crop on every page to contain page content.

Only PDF page boxes are changed; page content is not rasterized or rescaled.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from fractions import Fraction
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyMuPDF is required (import fitz failed): %s" % exc)

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise SystemExit("NumPy is required: %s" % exc)


@dataclass
class PageMeasure:
    page: int
    width_pt: float
    height_pt: float
    rotation_removed: int
    background_level: float
    content_bbox_pt: Optional[list[float]]
    padded_bbox_pt: Optional[list[float]]
    required_width_pt: float
    required_height_pt: float
    required_fraction: float
    crop_rect_pt: Optional[list[float]] = None


def clamp(value: float, low: float, high: float) -> float:
    if high < low:
        return low
    return max(low, min(high, value))


def parse_trim_proportion(raw: str) -> float:
    """Parse a user-facing trim proportion such as 2/3, 0.67, or 67%."""
    value = raw.strip().lower().replace(" ", "")
    aliases = {"all": 1.0, "full": 1.0, "none": 0.0}
    if value in aliases:
        return aliases[value]

    try:
        if value.endswith("%"):
            proportion = float(value[:-1]) / 100.0
        elif "/" in value:
            proportion = float(Fraction(value))
        else:
            proportion = float(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(
            "trim proportion must be a fraction, decimal, or percent such as 2/3, 0.67, or 67%"
        ) from exc

    if not 0.0 <= proportion <= 1.0:
        raise argparse.ArgumentTypeError("trim proportion must be between 0 and 1 inclusive")
    return proportion


def _bbox_from_mask(mask: np.ndarray, min_line_coverage: float) -> Optional[tuple[int, int, int, int]]:
    """Return x0, y0, x1, y1 in pixel edge coordinates, robust to sparse noise."""
    h, w = mask.shape
    if not mask.any():
        return None

    row_counts = mask.sum(axis=1)
    col_counts = mask.sum(axis=0)
    row_min = max(2, int(math.ceil(w * min_line_coverage)))
    col_min = max(2, int(math.ceil(h * min_line_coverage)))
    active_rows = np.flatnonzero(row_counts >= row_min)
    active_cols = np.flatnonzero(col_counts >= col_min)

    # If one projection is strong but the other is only one pixel thick, keep
    # the strong projection and derive the thin dimension from the raw mask.
    if active_rows.size and not active_cols.size:
        restricted = mask[active_rows[0] : active_rows[-1] + 1, :]
        active_cols = np.flatnonzero(restricted.any(axis=0))
    elif active_cols.size and not active_rows.size:
        restricted = mask[:, active_cols[0] : active_cols[-1] + 1]
        active_rows = np.flatnonzero(restricted.any(axis=1))

    if not active_rows.size or not active_cols.size:
        # Final fallback for very sparse but legitimate marks. Require enough
        # pixels that isolated scan noise does not drive the crop.
        ys, xs = np.nonzero(mask)
        if xs.size < 16:
            return None
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

    return (
        int(active_cols[0]),
        int(active_rows[0]),
        int(active_cols[-1]) + 1,
        int(active_rows[-1]) + 1,
    )


def detect_content_bbox(
    page: fitz.Page,
    dpi: int,
    white_threshold: int,
    min_line_coverage: float,
) -> tuple[Optional[fitz.Rect], float]:
    scale = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
    gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)

    # A high percentile adapts to slightly gray scanned paper while still
    # treating a full-page photo or dark background as content.
    background = float(np.percentile(gray, 99.0))
    cutoff = max(0.0, background - float(white_threshold))
    mask = gray < cutoff
    bbox_px = _bbox_from_mask(mask, min_line_coverage)
    if bbox_px is None:
        return None, background

    x0, y0, x1, y1 = bbox_px
    # get_pixmap renders the current visible CropBox, but pixel coordinates
    # start at (0, 0). Map them back into CropBox coordinates so a PDF that
    # was already cropped can be trimmed again without shifting the page.
    page_box = page.cropbox
    sx = page_box.width / float(pix.width)
    sy = page_box.height / float(pix.height)
    bbox = fitz.Rect(
        page_box.x0 + x0 * sx,
        page_box.y0 + y0 * sy,
        page_box.x0 + x1 * sx,
        page_box.y0 + y1 * sy,
    )
    return bbox, background


def inflate_bbox(bbox: fitz.Rect, page_rect: fitz.Rect, padding_ratio: float) -> fitz.Rect:
    pad_x = page_rect.width * padding_ratio
    pad_y = page_rect.height * padding_ratio
    return fitz.Rect(
        max(page_rect.x0, bbox.x0 - pad_x),
        max(page_rect.y0, bbox.y0 - pad_y),
        min(page_rect.x1, bbox.x1 + pad_x),
        min(page_rect.y1, bbox.y1 + pad_y),
    )


def required_crop_size(bbox: fitz.Rect, aspect: float) -> tuple[float, float]:
    # Width/height must have the document page aspect ratio and contain bbox.
    width = max(bbox.width, bbox.height * aspect)
    height = width / aspect
    return width, height


def place_common_crop(page_rect: fitz.Rect, bbox: Optional[fitz.Rect], width: float, height: float) -> fitz.Rect:
    if width > page_rect.width + 1e-6 or height > page_rect.height + 1e-6:
        raise ValueError("common crop does not fit inside page")

    if bbox is None:
        desired_x0 = page_rect.x0 + (page_rect.width - width) / 2.0
        desired_y0 = page_rect.y0 + (page_rect.height - height) / 2.0
        return fitz.Rect(desired_x0, desired_y0, desired_x0 + width, desired_y0 + height)

    desired_x0 = (bbox.x0 + bbox.x1 - width) / 2.0
    desired_y0 = (bbox.y0 + bbox.y1 - height) / 2.0

    # Feasible crop origins that both remain on-page and contain bbox.
    x_low = max(page_rect.x0, bbox.x1 - width)
    x_high = min(page_rect.x1 - width, bbox.x0)
    y_low = max(page_rect.y0, bbox.y1 - height)
    y_high = min(page_rect.y1 - height, bbox.y0)

    x0 = clamp(desired_x0, x_low, x_high)
    y0 = clamp(desired_y0, y_low, y_high)
    return fitz.Rect(x0, y0, x0 + width, y0 + height)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trim PDF whitespace proportionally and apply one crop size to all pages."
    )
    parser.add_argument("input_pdf")
    parser.add_argument("output_pdf")
    parser.add_argument(
        "--trim-proportion",
        required=True,
        type=parse_trim_proportion,
        help=(
            "Fraction of maximum removable whitespace to trim. "
            "Accepts values such as 2/3, 0.67, 67%%, all, or none."
        ),
    )
    parser.add_argument("--dpi", type=int, default=144, help="Detection render DPI (default: 144)")
    parser.add_argument(
        "--white-threshold",
        type=int,
        default=18,
        help="Difference below estimated paper white that counts as content (default: 18)",
    )
    parser.add_argument(
        "--min-line-coverage",
        type=float,
        default=0.002,
        help="Minimum row/column occupancy fraction used to reject isolated noise (default: 0.002)",
    )
    parser.add_argument(
        "--padding-ratio",
        type=float,
        default=0.005,
        help="Safety padding added around detected content as a fraction of page dimensions (default: 0.005)",
    )
    parser.add_argument(
        "--aspect-tolerance",
        type=float,
        default=0.0001,
        help="Numerical relative aspect-ratio tolerance across pages (default: 0.0001)",
    )
    parser.add_argument(
        "--main-tolerance",
        type=float,
        default=0.005,
        help="Pages within this fraction of the largest required crop are reported as main pages (default: 0.005)",
    )
    parser.add_argument(
        "--report-json",
        help="Optional path for a JSON report containing detected boxes, crop boxes, and main pages",
    )
    parser.add_argument(
        "--no-remove-rotation",
        action="store_true",
        help="Do not normalize page rotations before measurement; only use for known unrotated PDFs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dpi < 72:
        raise SystemExit("--dpi must be at least 72")
    if not (0 <= args.white_threshold <= 255):
        raise SystemExit("--white-threshold must be between 0 and 255")
    if not (0 <= args.min_line_coverage <= 0.1):
        raise SystemExit("--min-line-coverage must be between 0 and 0.1")
    if not (0 <= args.padding_ratio < 0.25):
        raise SystemExit("--padding-ratio must be between 0 and 0.25")

    input_path = Path(args.input_pdf)
    output_path = Path(args.output_pdf)
    if not input_path.is_file():
        raise SystemExit("Input PDF not found: %s" % input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.resolve() == input_path.resolve():
        raise SystemExit("Input and output paths must differ")

    doc = fitz.open(str(input_path))
    if doc.page_count == 0:
        raise SystemExit("Input PDF has no pages")

    rotations: list[int] = []
    if not args.no_remove_rotation:
        for page in doc:
            rotations.append(int(page.rotation))
            if page.rotation:
                page.remove_rotation()
    else:
        rotations = [int(page.rotation) for page in doc]
        if any(rotations):
            raise SystemExit(
                "--no-remove-rotation is only safe for PDFs whose pages already have rotation 0"
            )

    page_rects = [fitz.Rect(page.cropbox) for page in doc]
    aspects = [r.width / r.height for r in page_rects]
    aspect = float(np.median(aspects))
    for idx, a in enumerate(aspects, start=1):
        rel = abs(a - aspect) / aspect
        if rel > args.aspect_tolerance:
            raise SystemExit(
                "Pages do not share one aspect ratio after rotation normalization: "
                "page %d differs by %.4f%%. A single proportional crop cannot preserve all original aspect ratios."
                % (idx, rel * 100.0)
            )

    measures: list[PageMeasure] = []
    padded_boxes: list[Optional[fitz.Rect]] = []
    required_widths: list[float] = []

    for idx, page in enumerate(doc):
        page_rect = fitz.Rect(page.cropbox)
        bbox, bg = detect_content_bbox(page, args.dpi, args.white_threshold, args.min_line_coverage)
        padded = inflate_bbox(bbox, page_rect, args.padding_ratio) if bbox is not None else None
        if padded is None:
            req_w = 0.0
            req_h = 0.0
            req_fraction = 0.0
        else:
            req_w, req_h = required_crop_size(padded, aspect)
            req_fraction = max(req_w / page_rect.width, req_h / page_rect.height)
        padded_boxes.append(padded)
        required_widths.append(req_w)
        measures.append(
            PageMeasure(
                page=idx + 1,
                width_pt=round(page_rect.width, 4),
                height_pt=round(page_rect.height, 4),
                rotation_removed=rotations[idx] if not args.no_remove_rotation else 0,
                background_level=round(bg, 2),
                content_bbox_pt=[round(v, 4) for v in bbox] if bbox is not None else None,
                padded_bbox_pt=[round(v, 4) for v in padded] if padded is not None else None,
                required_width_pt=round(req_w, 4),
                required_height_pt=round(req_h, 4),
                required_fraction=round(req_fraction, 6),
            )
        )

    max_required_width = max(required_widths)
    min_width = min(r.width for r in page_rects)
    min_height = min(r.height for r in page_rects)
    # Largest common rectangle that fits every page while preserving the
    # shared aspect ratio. For equal-size documents this is the source size.
    baseline_width = min(min_width, min_height * aspect)
    baseline_height = baseline_width / aspect

    if max_required_width <= 1e-6:
        # All pages look blank. There is no evidence-based removable
        # whitespace, so preserve the largest common page size.
        full_trim_width = baseline_width
        full_trim_height = baseline_height
        main_pages: list[int] = []
    else:
        full_trim_width = max_required_width
        full_trim_height = full_trim_width / aspect
        main_pages = [
            i + 1
            for i, w in enumerate(required_widths)
            if w >= max_required_width * (1.0 - args.main_tolerance)
        ]

    if full_trim_width > baseline_width + 1e-6 or full_trim_height > baseline_height + 1e-6:
        raise SystemExit(
            "The common crop required by the largest content does not fit every page without scaling or padding. "
            "Required %.3f x %.3f pt, largest common page %.3f x %.3f pt."
            % (full_trim_width, full_trim_height, baseline_width, baseline_height)
        )

    # p is the fraction of maximum removable linear margin extent. With p=0
    # retain the largest common source size; with p=1 use the tightest safe
    # common crop; intermediate values preserve the aspect ratio exactly.
    target_width = baseline_width - args.trim_proportion * (baseline_width - full_trim_width)
    target_height = target_width / aspect

    for idx, page in enumerate(doc):
        crop = place_common_crop(fitz.Rect(page.cropbox), padded_boxes[idx], target_width, target_height)
        page.set_cropbox(crop)
        measures[idx].crop_rect_pt = [round(v, 4) for v in crop]

    # Preserve document structure as much as possible by changing page boxes in
    # the original PDF rather than rebuilding pages from raster output.
    doc.save(str(output_path), garbage=3, deflate=True, clean=False)
    doc.close()

    report = {
        "input_pdf": str(input_path),
        "output_pdf": str(output_path),
        "page_count": len(measures),
        "aspect_ratio": round(aspect, 8),
        "trim_proportion": round(args.trim_proportion, 8),
        "baseline_common_size_pt": [round(baseline_width, 4), round(baseline_height, 4)],
        "maximum_trim_crop_size_pt": [round(full_trim_width, 4), round(full_trim_height, 4)],
        "target_crop_size_pt": [round(target_width, 4), round(target_height, 4)],
        "maximum_removable_dimension_pt": [
            round(baseline_width - full_trim_width, 4),
            round(baseline_height - full_trim_height, 4),
        ],
        "applied_trim_dimension_pt": [
            round(baseline_width - target_width, 4),
            round(baseline_height - target_height, 4),
        ],
        "main_pages": main_pages,
        "detection": {
            "dpi": args.dpi,
            "white_threshold": args.white_threshold,
            "min_line_coverage": args.min_line_coverage,
            "padding_ratio": args.padding_ratio,
        },
        "pages": [asdict(m) for m in measures],
    }

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        "Trimmed %d pages at proportion %.6g to %.3f x %.3f pt; main page(s): %s"
        % (
            len(measures),
            args.trim_proportion,
            target_width,
            target_height,
            ", ".join(map(str, main_pages)) or "none (blank document)",
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
