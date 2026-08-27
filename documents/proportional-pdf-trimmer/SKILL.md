---
name: proportional-pdf-trimmer
description: Trim a user-specified proportion of removable whitespace from PDF pages while preserving the document page aspect ratio and enforcing one common output crop size across all pages. Use for PDFs with oversized margins, uneven whitespace, scanned or generated pages that should be uniformly cropped, or requests to identify the page(s) with the largest visual content footprint and use that footprint to determine a proportional crop for the whole document. Before trimming, ask how much removable whitespace to trim unless the user already supplied a proportion such as 2/3, 0.67, or 67%. Supports text, vector, image, and scanned PDFs through raster-based content detection while applying non-destructive PDF crop boxes.
---

# Proportional PDF Trimmer

Trim visible whitespace with `scripts/proportional_trim.py`. Keep page content vector/text-native by detecting from renders but applying PDF crop boxes rather than rasterizing the output.

## Required user input

Before processing, determine the requested whitespace trim proportion.

- If the user already supplied a proportion, use it directly.
- Otherwise ask: **"What proportion of the removable whitespace should I trim? For example: 2/3, 0.67, or 67%."**
- Do not silently assume a default proportion.
- Interpret `0` as no evidence-based whitespace removal, `1` or `100%` as the maximum safe trim, and values in between as partial trimming.
- Treat the proportion as the fraction of the maximum removable **linear margin extent** in width and height, not as a percentage of total page area. For example, `2/3` removes two-thirds of the width/height difference between the largest common source page size and the tightest safe common crop, leaving one-third of that removable margin.

## Workflow

1. Render the input PDF before editing and visually inspect representative pages, especially pages with unusually large or edge-adjacent content.
2. Obtain the trim proportion from the user as described above.
3. Run the trimmer with the explicit proportion and a JSON report:

```bash
python scripts/proportional_trim.py input.pdf output.pdf --trim-proportion 2/3 --report-json trim-report.json
```

4. Interpret `main_pages` as the page(s) that require the largest aspect-ratio-preserving crop after content detection and safety padding. The script computes the maximum safe common crop first, then interpolates from the largest common source page size toward that crop by the requested trim proportion.
5. Re-render the output with a renderer that visibly respects the PDF CropBox and compare it with the input. Confirm that no text, figures, annotations, or page-edge marks are clipped and that every visible page has the same width and height. Do not rely on a MediaBox-only render to verify cropping.
6. If content is clipped or faint marks were missed, rerun with a lower `--white-threshold`, higher `--dpi`, or larger `--padding-ratio`. If scanner noise prevents trimming, raise `--white-threshold` or `--min-line-coverage` cautiously.
7. Deliver only the final PDF unless the user asks for the JSON report.

## Crop geometry

For each page, detect a visual content bounding box from a grayscale render, add a small safety padding, then compute the smallest rectangle containing that box with the page's original width:height ratio. Select the largest such rectangle across the document as the **maximum-trim crop**, because smaller-content pages must not drive an over-aggressive crop.

Define the **baseline common size** as the largest aspect-ratio-preserving rectangle that fits every page. For a requested trim proportion `p` from 0 to 1, compute the final shared crop size by linear interpolation:

```text
final_width  = baseline_width  - p * (baseline_width  - maximum_trim_width)
final_height = baseline_height - p * (baseline_height - maximum_trim_height)
```

Because the baseline and maximum-trim rectangles have the same aspect ratio, every intermediate crop preserves that ratio exactly. Reposition a rectangle of exactly the final shared size independently on every page so each page's own content remains inside the crop whenever geometrically possible.

Treat pages within `--main-tolerance` of the largest required crop as co-main pages. Blank pages never drive the crop and receive a centered crop of the shared size.

## Constraints

- Require all pages to share one aspect ratio after rotation normalization. Stop with a clear error if page aspect ratios differ beyond a small numerical tolerance, because one common crop cannot preserve several different original aspect ratios simultaneously.
- Do not scale page content to force a fit. Stop if the common crop is physically larger than any page.
- Normalize rotated pages by default before measuring so crop coordinates remain stable while the visual orientation is preserved. Use `--no-remove-rotation` only for known unrotated inputs.
- Require `--trim-proportion` in the bundled script so standalone use cannot accidentally apply an unstated default.
- Prefer the bundled script over ad hoc PDF code so detection thresholds, crop placement, reporting, and failure behavior remain consistent.
- Follow the PDF render -> verify -> edit -> CropBox-aware re-render/compare workflow for every real document.
- Treat digitally signed PDFs as signature-sensitive: any crop-box edit changes the document after signing. Warn the user before proceeding when signatures matter.
- Treat uniform non-white or full-bleed backgrounds as a visual-QA edge case because adaptive background estimation can classify a uniform page background as removable margin even when the background is intentional design.

## Useful controls

- `--trim-proportion 2/3`: required fraction of maximum removable whitespace to trim. Also accepts decimals such as `0.67`, percentages such as `67%`, `all`, and `none`.
- `--dpi 144`: detection resolution. Raise for tiny text or hairlines.
- `--white-threshold 18`: how far a pixel must differ from estimated paper white to count as content. Lower values detect fainter marks; higher values suppress light scanner noise.
- `--min-line-coverage 0.002`: rejects sparse isolated noise from row/column bounds.
- `--padding-ratio 0.005`: adds a small safety margin around detected content before proportional fitting. Use `0` for the tightest crop.
- `--aspect-tolerance 0.0001`: numerical-only tolerance for tiny PDF dimension rounding differences; do not use it to merge genuinely different page aspect ratios.
- `--report-json PATH`: records the requested proportion, baseline common size, maximum-trim crop size, final target crop size, detected boxes, crop coordinates, and main pages.

## Example requests

- "Trim 2/3 of the removable whitespace from this PDF and make every page the same final size."
- "Trim the white margins from this PDF proportionally and ask me how much whitespace to remove first."
- "Find the page with the largest content area, preserve the page aspect ratio, then use that crop size for every page, but only remove 50% of the available whitespace."
- "Uniformly crop this scanned PDF without rescaling the contents."
