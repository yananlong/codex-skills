"""
JF Features extraction
Maintained by: AI Researchers
Purpose: Custom features via presidio feature computation
"""

from .presidio.feature_computation import add_custom_features_to_result


def extract_jf_features(data_dict):
    """Extract JF features using presidio feature computation."""
    add_custom_features_to_result(data_dict)
