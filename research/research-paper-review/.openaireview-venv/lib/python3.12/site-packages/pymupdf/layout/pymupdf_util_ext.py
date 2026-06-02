"""
PDF feature extraction utilities - Orchestrator
Purpose: Coordinate feature extractors (RF, IMF, YF, JF)
         Each extractor lives in its own module for independent maintenance.
"""

import traceback

from .pymupdf_util_base import make_custom_feature
from .pymupdf_util_rf import extract_rf_features
from .pymupdf_util_imf import image_feature_extraction_task
from .pymupdf_util_yf import extract_yf_features
from .pymupdf_util_jf import extract_jf_features


def apply_feature_extractors(data_dict, feature_set_name='rf+imf+yf',
                             feature_extractor=None, page=None, page_dict=None):
    """
    Apply experimental feature extractors to base data.

    Args:
        data_dict: Base data dictionary from extract_base_elements
        feature_set_name: String indicating which features to extract (e.g., 'rf+imf+yf')
        feature_extractor: ONNX model for image feature extraction
        page: PyMuPDF page object (required for YF features)
        page_dict: Page dictionary (required for YF features)

    Returns:
        data_dict: Enhanced with custom_features
    """
    # Initialize custom_features if not exists
    if 'custom_features' not in data_dict:
        _init_custom_features(data_dict)

    # Apply Image Model Features (IMF)
    if 'imf' in feature_set_name and feature_extractor is not None:
        try:
            page_img = data_dict['image']
            feature_map, bboxes_to_add, box_types_to_add = image_feature_extraction_task(
                page_img, feature_extractor, ('',)
            )
            data_dict['feature_map'] = feature_map

            # Add detected bboxes
            for bbox, type_val in zip(bboxes_to_add, box_types_to_add):
                if bbox not in data_dict['bboxes']:
                    data_dict['bboxes'].append(bbox)
                    data_dict['text'].append('')
                    if 'box_type' in data_dict:
                        data_dict['box_type'].append(type_val)

                    custom_feature = make_custom_feature(type_val, '')
                    data_dict['custom_features'].append(custom_feature)
        except Exception as exc:
            traceback.print_exc()
            print(f"Error in image feature extraction: {exc}")

    # Apply Robin's Features (RF)
    if 'rf' in feature_set_name:
        stext_page = data_dict.get('stext_page')
        if stext_page is not None:
            extract_rf_features(data_dict, stext_page)

    # Apply Youngmin's Features (YF)
    if 'yf' in feature_set_name:
        if page is not None and page_dict is not None:
            extract_yf_features(data_dict, page, page_dict)
    elif 'ymf' in feature_set_name and feature_extractor is not None:
        try:
            yfm = extract_yf_features(data_dict, page, page_dict, return_fet_map=True)
            page_img = data_dict['image']
            feature_map, bboxes_to_add, box_types_to_add = image_feature_extraction_task(
                page_img, feature_extractor, ('',), aug_fetmap=yfm,
            )
            data_dict['feature_map'] = feature_map
        except Exception as exc:
            traceback.print_exc()
            print(f"Error in image feature extraction: {exc}")

    # Apply JF features
    if 'jf' in feature_set_name:
        extract_jf_features(data_dict)

    return data_dict


def _init_custom_features(data_dict):
    """Initialize custom_features from box_type list."""
    data_dict['custom_features'] = []
    box_type = data_dict.get('box_type', [])

    for row_idx in range(len(data_dict['bboxes'])):
        bt = box_type[row_idx] if row_idx < len(box_type) else 'unknown'
        text = data_dict['text'][row_idx]
        data_dict['custom_features'].append(make_custom_feature(bt, text))
