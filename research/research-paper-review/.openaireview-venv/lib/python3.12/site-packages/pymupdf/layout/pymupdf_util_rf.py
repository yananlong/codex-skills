"""
Robin's Features (RF) extraction
Maintained by: PDF Engineers
Purpose: Extract text-based features from structured text page using PyMuPDF
"""

import pymupdf
import pymupdf.features as rf_features


def extract_rf_features(data_dict, stext_page):
    """Extract Robin's Features (RF) from structured text page."""
    has_non_invisible_text = False
    for row_idx, bbox in enumerate(data_dict['bboxes']):
        region = pymupdf.mupdf.FzRect(bbox[0], bbox[1], bbox[2], bbox[3])
        features = rf_features.fz_features_for_region(stext_page, region, 0)
        dd = data_dict['custom_features'][row_idx]
        for name in dir(features):
            if not name.startswith('_') and name not in ['this', 'thisown', 'last_char_rect']:
                dd[name] = getattr(features, name)
        if dd['num_numerals'] + dd['num_non_numerals'] > 0 and dd['invisible'] == 0:
            has_non_invisible_text = True

    if has_non_invisible_text:
        # Delete all the invisible text!
        for row_idx in range(len(data_dict['bboxes']) - 1, -1, -1):
            if data_dict['custom_features'][row_idx]['invisible'] == 1:
                del data_dict['custom_features'][row_idx]
                del data_dict['bboxes'][row_idx]
                del data_dict['text'][row_idx]
