# JSON Spec

Use `scripts/build_pdf_book.py <spec.json>`.

The script uses CLI PDF tools for the PDF mutations:
- `pdfseparate` to split selected pages
- `gs` to rotate landscape pages, apply crop boxes, and add bookmarks
- `pdfunite` to merge the ordered pages
- `pdfinfo` and `pdftoppm` for inspection

## Shape

```json
{
  "output": "/abs/or/relative/output.pdf",
  "inputs": [
    {
      "path": "/abs/or/relative/source.pdf",
      "start_page": 1,
      "end_page": 10,
      "drop_first_page": false
    }
  ],
  "normalize_portrait": true,
  "crop_whitespace": {
    "render_dpi": 96,
    "threshold": 245,
    "padding_ratio": 0.01
  },
  "bookmarks": [
    { "title": "Chapter 1", "page": 1, "level": 1 },
    { "title": "Section 1.1", "page": 3, "level": 2 }
  ]
}
```

## Fields

- `output`: Required. Relative paths are resolved from the spec file directory.
- `inputs`: Required, ordered list.
- `inputs[].path`: Required.
- `inputs[].start_page`: Optional, 1-based inclusive. Defaults to `1`.
- `inputs[].end_page`: Optional, 1-based inclusive. Defaults to the last page.
- `inputs[].drop_first_page`: Optional. When `true`, increment the effective start page by 1. Use this for JSTOR/cover sheets.
- `normalize_portrait`: Optional boolean. When `true`, split to single-page PDFs and rotate only the landscape pages with Ghostscript.
- `crop_whitespace`: Optional. Omit or set to `false` to disable.
- `crop_whitespace.render_dpi`: Raster DPI for whitespace detection. Default `96`.
- `crop_whitespace.threshold`: Grayscale cutoff; lower means less aggressive whitespace detection. Default `245`.
- `crop_whitespace.padding_ratio`: Fraction of page width/height to keep as padding after the common crop is computed. Default `0.01`.
- `bookmarks`: Optional ordered outline list.
- `bookmarks[].title`: Required bookmark title.
- `bookmarks[].page`: Required, 1-based output PDF page.
- `bookmarks[].level`: Optional outline depth. Default `1`. Use `2` for section bookmarks under the previous level-1 chapter, `3` for subsections, and so on. Do not skip levels.

## Notes

- Bookmark pages are output PDF pages after all `drop_first_page`, `start_page`, and `end_page` rules are applied.
- Cropping is common and proportional across pages: the script finds the smallest whitespace margin shared across nonblank pages, subtracts `padding_ratio`, and applies the same relative crop to every page.
- The script prints a JSON summary with `pages`, `rotated_pages`, `crop_margins`, and `page_map`.

## Example: Drop JSTOR Pages And Add Chapter Bookmarks

```json
{
  "output": "book-clean.pdf",
  "inputs": [
    { "path": "Huat-FrontMatter-2024.pdf", "drop_first_page": true },
    { "path": "Huat-TableContents-2024.pdf", "drop_first_page": true },
    { "path": "Huat-Preface-2024.pdf", "drop_first_page": true }
  ],
  "normalize_portrait": true,
  "bookmarks": [
    { "title": "Front Matter", "page": 1, "level": 1 },
    { "title": "Contents", "page": 6, "level": 1 },
    { "title": "Preface", "page": 8, "level": 1 }
  ]
}
```

## Example: Chapter And Section Outline

```json
{
  "output": "chapter-bookmarked.pdf",
  "inputs": [
    { "path": "book.pdf" }
  ],
  "bookmarks": [
    { "title": "Chapter One", "page": 19, "level": 1 },
    { "title": "Kampong Life", "page": 30, "level": 2 },
    { "title": "Colonial Administrative View of the Kampong", "page": 32, "level": 2 },
    { "title": "Chapter Two", "page": 41, "level": 1 }
  ]
}
```
