"""
Custom feature computation for PyMuPDF extraction results.

This module computes additional features (char_count, word_count, etc.) from
PyMuPDF's text extraction results. These features are computed separately from
PyMuPDF's native features to enable caching in prepare_data.py.
"""

from typing import Dict, List


def compute_features_from_text(text, bbox, existing_features):
    """
    Compute custom features from text string and bbox.

    Args:
        text: Text string from PyMuPDF
        bbox: Bounding box [x0, y0, x1, y1]
        existing_features: Existing features dict from PyMuPDF

    Returns:
        Dict of computed features
    """
    text_str = str(text) if text else ""

    # Compute text-based features
    char_count = len(text_str)
    word_count = len(text_str.split()) if text_str.strip() else 0
    sentence_count = text_str.count('.') + text_str.count('!') + text_str.count('?')
    digit_count = sum(c.isdigit() for c in text_str)
    capital_count = sum(c.isupper() for c in text_str)
    punctuation_count = sum(c in '.,!?;:()[]{}"\'/-' for c in text_str)
    whitespace_count = sum(c.isspace() for c in text_str)

    # Get bbox dimensions
    block_width = bbox[2] - bbox[0] if len(bbox) >= 4 else 0.0
    block_height = bbox[3] - bbox[1] if len(bbox) >= 4 else 0.0
    block_area = block_width * block_height if block_width > 0 and block_height > 0 else 1.0

    # Get font info from existing features
    font_size = existing_features.get('font_size', 12.0)
    font_size_max = existing_features.get('font_size_max', font_size)
    font_size_min = existing_features.get('font_size_min', font_size)
    font_size_variance = existing_features.get('font_size_variance', 0.0)
    is_bold = existing_features.get('is_bold', 0)
    is_italic = existing_features.get('is_italic', 0)
    is_underline = existing_features.get('is_underline', 0)

    # Get line info from existing features
    num_lines = existing_features.get('num_lines', 1)
    avg_line_height = block_height / num_lines if num_lines > 0 else block_height
    avg_line_length = char_count / num_lines if num_lines > 0 else char_count
    max_line_length = char_count  # Approximate
    avg_line_spacing = existing_features.get('avg_line_spacing', 0.0)
    first_line_indent = existing_features.get('first_line_indent', 0.0)

    # Compute derived features
    aspect_ratio = block_width / block_height if block_height > 0 else 0.0
    text_density = char_count / block_area if block_area > 0 else 0.0
    font_color_grayscale = existing_features.get('font_color_grayscale', 0.0)

    return {
        'char_count': char_count,
        'word_count': word_count,
        'sentence_count': sentence_count,
        'digit_count': digit_count,
        'capital_count': capital_count,
        'punctuation_count': punctuation_count,
        'whitespace_count': whitespace_count,
        'font_size_max': font_size_max,
        'font_size_min': font_size_min,
        'font_size_variance': font_size_variance,
        'is_bold': is_bold,
        'is_italic': is_italic,
        'is_underline': is_underline,
        'block_width': block_width,
        'block_height': block_height,
        'aspect_ratio': aspect_ratio,
        'text_density': text_density,
        'font_color_grayscale': font_color_grayscale,
        'avg_line_height': avg_line_height,
        'avg_line_spacing': avg_line_spacing,
        'avg_line_length': avg_line_length,
        'max_line_length': max_line_length,
        'first_line_indent': first_line_indent,
    }


def add_custom_features_to_result(result: Dict) -> Dict:
    """
    Add custom features to PyMuPDF extraction result.
    This allows features to be cached along with PyMuPDF data.

    Args:
        result: Dict with 'bboxes', 'custom_features', 'text' keys

    Returns:
        Modified result dict with custom features added
    """
    custom_features_list = result.get('custom_features', [])
    pymupdf_bboxes = result.get('bboxes', [])
    pymupdf_texts = result.get('text', [])

    if not custom_features_list or not pymupdf_bboxes:
        return result

    # Compute features directly from PyMuPDF's text (trust the text from PyMuPDF)
    try:
        if pymupdf_texts and len(pymupdf_texts) == len(custom_features_list):
            for i, text in enumerate(pymupdf_texts):
                if i >= len(custom_features_list):
                    break

                # Get bbox for computing dimensions
                bbox = pymupdf_bboxes[i] if i < len(pymupdf_bboxes) else [0, 0, 0, 0]
                existing_features = custom_features_list[i]

                # Compute features from text
                features = compute_features_from_text(text, bbox, existing_features)
                custom_features_list[i].update(features)
        else:
            # If text is not available, add zero features to maintain consistency
            for i in range(len(custom_features_list)):
                custom_features_list[i].update({
                    'char_count': 0, 'word_count': 0, 'sentence_count': 0,
                    'digit_count': 0, 'capital_count': 0, 'punctuation_count': 0,
                    'whitespace_count': 0, 'font_size_max': 0.0, 'font_size_min': 0.0,
                    'font_size_variance': 0.0, 'is_bold': 0, 'is_italic': 0,
                    'is_underline': 0, 'block_width': 0.0, 'block_height': 0.0,
                    'aspect_ratio': 0.0, 'text_density': 0.0, 'font_color_grayscale': 0.0,
                    'avg_line_height': 0.0, 'avg_line_spacing': 0.0, 'avg_line_length': 0.0,
                    'max_line_length': 0, 'first_line_indent': 0.0,
                })
    except Exception as e:
        # If we fail to add custom features, just return original data
        # This ensures we don't break the pipeline
        pass

    return result
