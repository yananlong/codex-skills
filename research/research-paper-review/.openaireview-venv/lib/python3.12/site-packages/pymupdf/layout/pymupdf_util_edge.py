"""
Edge feature computation module
Maintained by: PDF Engineers (edge_type implementations) + AI Researchers (orchestration)
Purpose: Compute edge attributes for graph neural network input

Edge types:
    - default: Relative bbox geometry (get_edge_transform_bbox)
    - SEO: Default + alignment features (get_edge_transform_bbox_add_alignment)
    - PRS: Presidio spatial features (compute_edge_features)

To add a new edge type:
    1. Implement compute function in this file
    2. Register it in get_edge_attr()
"""

import numpy as np

from .common_util import (get_edge_by_directional_nn, get_edge_by_alignment,
                          get_edge_transform_bbox, get_edge_transform_bbox_add_alignment)
from .roi_pooling import extract_bbox_features_by_roi_pooling


def get_edge_attr(bboxes, edge_index, edge_type='', data_dict=None, page_img=None):
    """
    Compute edge attributes based on edge type.

    Args:
        bboxes: np.ndarray of shape (N, 4), float32
        edge_index: list of (i, j) tuples
        edge_type: str — '', 'SEO', 'PRS', etc.
        page_img: page image array (required for 'PRS')

    Returns:
        edge_attr: np.ndarray of shape (E, D)
    """
    if edge_type == 'SEO':
        return get_edge_transform_bbox_add_alignment(bboxes, edge_index)

    elif edge_type == 'PRS':
        from .presidio.graph import compute_edge_features
        page_h, page_w, _ = page_img.shape
        temp_edge_idx = np.array(edge_index).T
        return compute_edge_features(node_bboxes=bboxes, edge_index=temp_edge_idx,
                                     page_width=page_w, page_height=page_h)

    else:
        return get_edge_transform_bbox(bboxes, edge_index)


def get_edge_dim(edge_type='', page_img=None):
    """
    Get edge attribute dimension by computing on dummy data.
    Used for single-node edge case.

    Args:
        edge_type: str
        page_img: page image array (required for 'PRS')

    Returns:
        int: edge feature dimension
    """
    dummy_bboxes = np.array([
        [0.0, 0.0, 10.0, 10.0],
        [20.0, 20.0, 30.0, 30.0]
    ], dtype=np.float32)
    dummy_edge_index = [(0, 1), (1, 0)]
    dummy_attr = get_edge_attr(dummy_bboxes, dummy_edge_index, edge_type, page_img=page_img)
    return dummy_attr.shape[1]


def build_edge_index(bboxes, edge_sampling='4D'):
    """
    Build edge index from bboxes.

    Args:
        bboxes: np.ndarray of shape (N, 4)
        edge_sampling: '4D' (directional NN) or '4D+AL' (directional NN + alignment)

    Returns:
        edge_index: list of (i, j) tuples
    """
    if edge_sampling == '4D+AL':
        edge_index1, _ = get_edge_by_directional_nn(bboxes, 50000, vertical_gap=0.3)
        edge_index2 = get_edge_by_alignment(bboxes, dist_threshold=0)
        edge_index = sorted(set(edge_index1 + edge_index2))
    else:
        edge_index, _ = get_edge_by_directional_nn(bboxes, 50000, vertical_gap=0.3)
    return edge_index


def append_image_edge_features(edge_attr, edge_index, original_bboxes, feature_map, page_w, page_h):
    """
    Append ROI-pooled image features to edge attributes.

    Args:
        edge_attr: existing edge attributes, shape (E, D)
        edge_index: np.ndarray of shape (2, E)
        original_bboxes: list of [x1, y1, x2, y2]
        feature_map: neural network feature map
        page_w, page_h: page dimensions

    Returns:
        edge_attr: np.ndarray of shape (E, D + D_img)
    """
    edge_bboxes = []
    row, col = edge_index
    for node_idx_1, node_idx_2 in zip(row, col):
        bbox1 = original_bboxes[node_idx_1]
        bbox2 = original_bboxes[node_idx_2]
        x1 = min(bbox1[0], bbox2[0])
        y1 = min(bbox1[1], bbox2[1])
        x2 = max(bbox1[2], bbox2[2])
        y2 = max(bbox1[3], bbox2[3])
        edge_bboxes.append([x1, y1, x2, y2])

    edge_features = extract_bbox_features_by_roi_pooling(
        feature_map, edge_bboxes, page_w, page_h,
        apply_softmax=False, concat_mean_max=True, add_uncertainty=False
    )
    return np.concatenate([edge_attr, edge_features], axis=1)
