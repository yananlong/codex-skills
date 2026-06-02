from __future__ import annotations

import numpy as np
from typing import List, Optional, Tuple

try:
    from scipy.spatial import cKDTree  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cKDTree = None


def find_directional_neighbors(node_bboxes: np.ndarray, max_gap_distance: float) -> Tuple[np.ndarray, np.ndarray]:
    N = node_bboxes.shape[0]
    edges = []
    directions = []

    x0, y0, x1, y1 = node_bboxes[:, 0], node_bboxes[:, 1], node_bboxes[:, 2], node_bboxes[:, 3]
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0

    for i in range(N):
        above_mask = (y0 > y1[i])
        if np.any(above_mask):
            above_indices = np.where(above_mask)[0]
            horizontal_overlaps = np.maximum(
                0, np.minimum(x1[above_indices], x1[i]) - np.maximum(x0[above_indices], x0[i])
            )
            valid_above = above_indices[horizontal_overlaps > 0]
            if len(valid_above) > 0:
                y_gaps = y0[valid_above] - y1[i]
                x_distances = np.abs(cx[valid_above] - cx[i])
                distances = y_gaps * 2.0 + x_distances
                closest_idx = valid_above[np.argmin(distances)]
                if distances[np.argmin(distances)] <= max_gap_distance:
                    edges.append([i, closest_idx])
                    directions.append(0)

        below_mask = (y1 < y0[i])
        if np.any(below_mask):
            below_indices = np.where(below_mask)[0]
            horizontal_overlaps = np.maximum(
                0, np.minimum(x1[below_indices], x1[i]) - np.maximum(x0[below_indices], x0[i])
            )
            valid_below = below_indices[horizontal_overlaps > 0]
            if len(valid_below) > 0:
                y_gaps = y0[i] - y1[valid_below]
                x_distances = np.abs(cx[valid_below] - cx[i])
                distances = y_gaps * 2.0 + x_distances
                closest_idx = valid_below[np.argmin(distances)]
                if distances[np.argmin(distances)] <= max_gap_distance:
                    edges.append([i, closest_idx])
                    directions.append(1)

        left_mask = (x1 < x0[i])
        if np.any(left_mask):
            left_indices = np.where(left_mask)[0]
            vertical_overlaps = np.maximum(
                0, np.minimum(y1[left_indices], y1[i]) - np.maximum(y0[left_indices], y0[i])
            )
            valid_left = left_indices[vertical_overlaps > 0]
            if len(valid_left) > 0:
                x_gaps = x0[i] - x1[valid_left]
                y_distances = np.abs(cy[valid_left] - cy[i])
                distances = x_gaps * 2.0 + y_distances
                closest_idx = valid_left[np.argmin(distances)]
                if distances[np.argmin(distances)] <= max_gap_distance:
                    edges.append([i, closest_idx])
                    directions.append(2)

        right_mask = (x0 > x1[i])
        if np.any(right_mask):
            right_indices = np.where(right_mask)[0]
            vertical_overlaps = np.maximum(
                0, np.minimum(y1[right_indices], y1[i]) - np.maximum(y0[right_indices], y0[i])
            )
            valid_right = right_indices[vertical_overlaps > 0]
            if len(valid_right) > 0:
                x_gaps = x0[valid_right] - x1[i]
                y_distances = np.abs(cy[valid_right] - cy[i])
                distances = x_gaps * 2.0 + y_distances
                closest_idx = valid_right[np.argmin(distances)]
                if distances[np.argmin(distances)] <= max_gap_distance:
                    edges.append([i, closest_idx])
                    directions.append(3)

    if len(edges) == 0:
        return np.array([[], []], dtype=np.int64), np.array([], dtype=np.int64)

    edge_index = np.array(edges, dtype=np.int64).T
    edge_directions = np.array(directions, dtype=np.int64)
    return edge_index, edge_directions


def find_alignment_edges(
        node_bboxes: np.ndarray,
        tolerance: float = 3.0,
        max_distance: Optional[float] = None,
        page_width: Optional[float] = None,
        page_height: Optional[float] = None,
) -> np.ndarray:
    N = node_bboxes.shape[0]
    if N <= 1:
        return np.array([[], []], dtype=np.int64)

    x0, y0, x1, y1 = node_bboxes[:, 0], node_bboxes[:, 1], node_bboxes[:, 2], node_bboxes[:, 3]
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0

    edges = []
    for i in range(N):
        for j in range(i + 1, N):
            if max_distance is not None:
                dx = cx[j] - cx[i]
                dy = cy[j] - cy[i]
                if np.sqrt(dx * dx + dy * dy) > max_distance:
                    continue

            aligned_x = (
                    abs(x0[i] - x0[j]) <= tolerance
                    or abs(x1[i] - x1[j]) <= tolerance
                    or abs(cx[i] - cx[j]) <= tolerance
            )
            aligned_y = (
                    abs(y0[i] - y0[j]) <= tolerance
                    or abs(y1[i] - y1[j]) <= tolerance
                    or abs(cy[i] - cy[j]) <= tolerance
            )

            if aligned_x or aligned_y:
                edges.append([i, j])
                edges.append([j, i])

    if not edges:
        return np.array([[], []], dtype=np.int64)
    return np.array(edges, dtype=np.int64).T


def find_knn_edges(node_bboxes: np.ndarray, k: int = 6) -> np.ndarray:
    N = node_bboxes.shape[0]
    if N <= 1 or k <= 0:
        return np.array([[], []], dtype=np.int64)

    cx = (node_bboxes[:, 0] + node_bboxes[:, 2]) / 2.0
    cy = (node_bboxes[:, 1] + node_bboxes[:, 3]) / 2.0
    centers = np.stack([cx, cy], axis=1)

    if cKDTree is not None:
        tree = cKDTree(centers)
        k_query = min(k + 1, N)
        _, indices = tree.query(centers, k=k_query)
        if indices.ndim == 1:
            return np.array([[], []], dtype=np.int64)
        neighbor_indices = indices[:, 1:]
        k_actual = neighbor_indices.shape[1]
        src = np.repeat(np.arange(N), k_actual)
        dst = neighbor_indices.flatten()
        return np.stack([src, dst], axis=0).astype(np.int64)

    edges = []
    indices = np.arange(N)
    for i in range(N):
        diffs = centers - centers[i]
        d2 = diffs[:, 0] ** 2 + diffs[:, 1] ** 2
        d2[i] = np.inf
        order = np.lexsort((indices, d2))
        nn_idx = order[: min(k, N - 1)]
        for j in nn_idx:
            edges.append([i, int(j)])
    if not edges:
        return np.array([[], []], dtype=np.int64)
    return np.array(edges, dtype=np.int64).T


def compute_sce_edge_features_18(
        node_bboxes: np.ndarray,
        edge_index: np.ndarray,
) -> np.ndarray:
    """
    Compute SCE-style 18-d edge features (relative positions, scale, enclosing box).
    See external/sce train/infer/common_util get_edge_transform_bbox and docs/EDGE_FEATURES.md.

    S = source (edge_index[0]), O = target (edge_index[1]). R = enclosing bbox of S and O.
    Bboxes [x0, y0, x1, y1] (same as Presidio).

    Returns:
        [E, 18] float32.
    """
    E = edge_index.shape[1]
    if E == 0:
        return np.zeros((0, 18), dtype=np.float32)

    eps = 1e-6
    S = node_bboxes[edge_index[0]]
    O = node_bboxes[edge_index[1]]

    sw = S[:, 2] - S[:, 0]
    sh = S[:, 3] - S[:, 1]
    ow = O[:, 2] - O[:, 0]
    oh = O[:, 3] - O[:, 1]

    R_x1 = np.minimum(S[:, 0], O[:, 0])
    R_y1 = np.minimum(S[:, 1], O[:, 1])
    R_x2 = np.maximum(S[:, 2], O[:, 2])
    R_y2 = np.maximum(S[:, 3], O[:, 3])
    rw = R_x2 - R_x1
    rh = R_y2 - R_y1

    safe = lambda x: np.where(x <= 0, eps, x)
    sw_ = safe(sw)
    sh_ = safe(sh)
    ow_ = safe(ow)
    oh_ = safe(oh)
    rw_ = safe(rw)
    rh_ = safe(rh)

    f = []
    f.append((S[:, 0] - O[:, 0]) / sw_)
    f.append((S[:, 1] - O[:, 1]) / sh_)
    f.append((O[:, 0] - S[:, 0]) / ow_)
    f.append((O[:, 1] - S[:, 1]) / oh_)
    f.append(np.log(sw_ / ow_))
    f.append(np.log(sh_ / oh_))
    f.append((S[:, 0] - R_x1) / sw_)
    f.append((S[:, 1] - R_y1) / sh_)
    f.append((R_x1 - S[:, 0]) / rw_)
    f.append((R_y1 - S[:, 1]) / rh_)
    f.append(np.log(sw_ / rw_))
    f.append(np.log(sh_ / rh_))
    f.append((O[:, 0] - R_x1) / ow_)
    f.append((O[:, 1] - R_y1) / oh_)
    f.append((R_x1 - O[:, 0]) / rw_)
    f.append((R_y1 - O[:, 1]) / rh_)
    f.append(np.log(ow_ / rw_))
    f.append(np.log(oh_ / rh_))

    out = np.stack(f, axis=1).astype(np.float32)
    return np.nan_to_num(out, nan=0.0, posinf=1e5, neginf=-1e5)


def compute_edge_features(
        node_bboxes: np.ndarray,
        edge_index: np.ndarray,
        page_width: float,
        page_height: float,
        edge_directions: Optional[np.ndarray] = None,
        node_font_sizes: Optional[np.ndarray] = None,
        node_draw_orders: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute edge features for each edge (vectorized).
    Appends SCE 18-d features (see compute_sce_edge_features_18) ¡æ [E, 43].

    Edge features (25-d base):
    - normalized_dx = (cx_j - cx_i) / page_width
    - normalized_dy = (cy_j - cy_i) / page_height
    - signed_gap_x (horizontal gap)
    - signed_gap_y (vertical gap)
    - x_overlap_ratio
    - y_overlap_ratio
    - log(w_j / w_i) (relative width ratio)
    - log(h_j / h_i) (relative height ratio)
    - delta_left = (x0_j - x0_i) / page_width (left-to-left delta)
    - delta_right = (x1_j - x1_i) / page_width (right-to-right delta)
    - delta_center_horizontal = (cx_j - cx_i) / page_width (horizontal center delta)
    - delta_top = (y0_j - y0_i) / page_height (top edge delta)
    - delta_bottom = (y1_j - y1_i) / page_height (bottom edge delta)
    - delta_middle = (cy_j - cy_i) / page_height (vertical center/middle delta)
    - iou = intersection_area / union_area (Intersection over Union - 2D overlap)
    - ioa_i = intersection_area / area_i (Intersection over Area of node i)
    - ioa_j = intersection_area / area_j (Intersection over Area of node j)
    - direction one-hot: {up, down, left, right, other} (5 dims)
    - font_log_ratio = log(font_size_u / font_size_v) (font size contrast)
    - font_abs_log_ratio = |log(font_size_u / font_size_v)| (absolute font size contrast)
    - delta_draw_order = draw_order_j - draw_order_i (difference of normalized draw orders)

    Args:
        node_bboxes: Array of shape [N, 4] - [x0, y0, x1, y1]
        edge_index: Array of shape [2, E] - edge indices
        page_width: Page width in points
        page_height: Page height in points
        edge_directions: Optional array of shape [E] - direction labels (0=up, 1=down, 2=left, 3=right)
        node_font_sizes: Optional array of shape [N] - font sizes per node (font_size_median or font_size)
        node_draw_orders: Optional array of shape [N] - draw order indices (0-indexed) per node

    Returns:
        Edge feature matrix [E, 43].
    """
    E = edge_index.shape[1]
    if E == 0:
        return np.zeros((0, 43), dtype=np.float32)

    # Extract coordinates for all nodes
    x0, y0, x1, y1 = node_bboxes[:, 0], node_bboxes[:, 1], node_bboxes[:, 2], node_bboxes[:, 3]
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    w = x1 - x0
    h = y1 - y0

    # Get source and target indices for all edges
    src = edge_index[0]  # [E]
    dst = edge_index[1]  # [E]

    # Vectorized: get coordinates for source and target nodes
    x0_i, y0_i, x1_i, y1_i = x0[src], y0[src], x1[src], y1[src]
    x0_j, y0_j, x1_j, y1_j = x0[dst], y0[dst], x1[dst], y1[dst]
    cx_i, cy_i = cx[src], cy[src]
    cx_j, cy_j = cx[dst], cy[dst]
    w_i, h_i = w[src], h[src]
    w_j, h_j = w[dst], h[dst]

    # Normalized deltas
    dx = (cx_j - cx_i) / page_width
    dy = (cy_j - cy_i) / page_height

    # Signed gaps (vectorized)
    # Horizontal gap
    gap_x = np.zeros(E, dtype=np.float32)
    left_of = x1_i < x0_j  # i is left of j
    right_of = x1_j < x0_i  # j is left of i
    gap_x[left_of] = x0_j[left_of] - x1_i[left_of]
    gap_x[right_of] = -(x0_i[right_of] - x1_j[right_of])
    # Overlap case: gap_x stays 0

    # Vertical gap
    gap_y = np.zeros(E, dtype=np.float32)
    above = y1_i < y0_j  # i is above j
    below = y1_j < y0_i  # j is above i
    gap_y[above] = y0_j[above] - y1_i[above]
    gap_y[below] = -(y0_i[below] - y1_j[below])
    # Overlap case: gap_y stays 0

    # Overlap ratios
    x_overlap = np.maximum(0, np.minimum(x1_i, x1_j) - np.maximum(x0_i, x0_j))
    y_overlap = np.maximum(0, np.minimum(y1_i, y1_j) - np.maximum(y0_i, y0_j))
    x_overlap_ratio = x_overlap / np.maximum(np.maximum(w_i, w_j), 1e-6)
    y_overlap_ratio = y_overlap / np.maximum(np.maximum(h_i, h_j), 1e-6)

    # Compute 2D overlap metrics: IoU and IoA
    intersection_area = x_overlap * y_overlap  # [E] - intersection area
    area_i = w_i * h_i  # [E] - area of node i
    area_j = w_j * h_j  # [E] - area of node j
    union_area = area_i + area_j - intersection_area  # [E] - union area

    # IoU (Intersection over Union) - standard 2D overlap metric
    iou = intersection_area / np.maximum(union_area, 1e-6)  # [E]

    # IoA_i (Intersection over Area of node i) - how much of node i is covered by intersection
    ioa_i = intersection_area / np.maximum(area_i, 1e-6)  # [E]

    # IoA_j (Intersection over Area of node j) - how much of node j is covered by intersection
    ioa_j = intersection_area / np.maximum(area_j, 1e-6)  # [E]

    # Relative size ratios (log)
    log_w_ratio = np.log(np.maximum(w_j / np.maximum(w_i, 1e-6), 1e-6))
    log_h_ratio = np.log(np.maximum(h_j / np.maximum(h_i, 1e-6), 1e-6))

    # Direction one-hot (5 dims: up, down, left, right, other)
    direction_onehot = np.zeros((E, 5), dtype=np.float32)

    if edge_directions is not None and len(edge_directions) == E:
        # Use provided directions
        valid_dirs = (edge_directions >= 0) & (edge_directions <= 3)
        direction_onehot[valid_dirs, edge_directions[valid_dirs]] = 1.0
        direction_onehot[~valid_dirs, 4] = 1.0  # other
    else:
        # Infer direction from geometry
        abs_dx = np.abs(dx)
        abs_dy = np.abs(dy)

        vertical = abs_dx < abs_dy
        horizontal = abs_dx > abs_dy
        diagonal = ~vertical & ~horizontal

        down = vertical & (dy > 0)
        up = vertical & (dy <= 0)
        right = horizontal & (dx > 0)
        left = horizontal & (dx <= 0)

        direction_onehot[up, 0] = 1.0
        direction_onehot[down, 1] = 1.0
        direction_onehot[left, 2] = 1.0
        direction_onehot[right, 3] = 1.0
        direction_onehot[diagonal, 4] = 1.0

    # Left-to-left and right-to-right deltas (normalized)
    delta_left = (x0_j - x0_i) / page_width  # Left edge delta
    delta_right = (x1_j - x1_i) / page_width  # Right edge delta

    # Additional edge deltas
    delta_center_horizontal = (cx_j - cx_i) / page_width  # Horizontal center delta
    delta_top = (y0_j - y0_i) / page_height  # Top edge delta
    delta_bottom = (y1_j - y1_i) / page_height  # Bottom edge delta
    delta_middle = (cy_j - cy_i) / page_height  # Vertical center (middle) delta

    # Stack all features [E, 17] (was 14, now includes IoU, IoA_i, IoA_j)
    features = np.stack([
        dx, dy,
        gap_x / page_width,
        gap_y / page_height,
        x_overlap_ratio,
        y_overlap_ratio,
        log_w_ratio,
        log_h_ratio,
        delta_left,  # Left-to-left delta
        delta_right,  # Right-to-right delta
        delta_center_horizontal,  # Horizontal center delta
        delta_top,  # Top edge delta
        delta_bottom,  # Bottom edge delta
        delta_middle,  # Vertical center (middle) delta
        iou,  # IoU (Intersection over Union) - 2D overlap metric
        ioa_i,  # IoA_i (Intersection over Area of node i)
        ioa_j,  # IoA_j (Intersection over Area of node j)
    ], axis=1).astype(np.float32)

    # Concatenate with direction one-hot [E, 22] (was 19, now 22)
    edge_features = np.concatenate([features, direction_onehot], axis=1)

    # Add font-size contrast features (always include, set to 0 if font sizes not available)
    if node_font_sizes is not None and len(node_font_sizes) > 0:
        # Get font sizes for source and target nodes
        font_size_i = node_font_sizes[src]  # [E]
        font_size_j = node_font_sizes[dst]  # [E]

        # Handle edge cases: nodes with no text (font_size = 0 or invalid)
        EPS = 1e-6
        MIN_FONT_SIZE = 1.0  # Minimum valid font size

        # Clamp font sizes to avoid extreme ratios
        font_size_i_safe = np.maximum(font_size_i, MIN_FONT_SIZE)
        font_size_j_safe = np.maximum(font_size_j, MIN_FONT_SIZE)

        # Compute font size ratio (u / v)
        font_ratio = font_size_i_safe / np.maximum(font_size_j_safe, EPS)

        # Clamp extreme ratios to avoid outliers (e.g., 0.1 to 10.0)
        MAX_RATIO = 10.0
        MIN_RATIO = 0.1
        font_ratio = np.clip(font_ratio, MIN_RATIO, MAX_RATIO)

        # Log-ratio: log(u / v) - symmetric around 0, order-aware
        font_log_ratio = np.log(font_ratio)  # [E]

        # Absolute log-ratio: |log(u / v)| - magnitude of contrast
        font_abs_log_ratio = np.abs(font_log_ratio)  # [E]

        # Validity flag: 1 if both nodes have valid font sizes, 0 otherwise
        valid_i = (font_size_i >= MIN_FONT_SIZE) & (font_size_i < 1000.0)  # Reasonable upper bound
        valid_j = (font_size_j >= MIN_FONT_SIZE) & (font_size_j < 1000.0)
        font_valid = (valid_i & valid_j).astype(np.float32)  # [E]

        # For invalid edges, set log-ratio to 0 and validity to 0
        font_log_ratio = font_log_ratio * font_valid
        font_abs_log_ratio = font_abs_log_ratio * font_valid

        # Stack font features [E, 2]
        font_features = np.stack([
            font_log_ratio,  # Signed log-ratio (direction matters)
            font_abs_log_ratio,  # Absolute log-ratio (magnitude of contrast)
        ], axis=1).astype(np.float32)
    else:
        # No font sizes available: set font features to 0
        font_features = np.zeros((E, 2), dtype=np.float32)

    # Concatenate font features [E, 24] (22 base + direction + 2 font)
    edge_features = np.concatenate([edge_features, font_features], axis=1)

    if node_draw_orders is not None and len(node_draw_orders) > 0:
        draw_order_i = node_draw_orders[src]
        draw_order_j = node_draw_orders[dst]
        delta_draw_order = draw_order_j - draw_order_i
        # Clamp to [-10, 10] and normalize to [-1, 1]
        delta_draw_order = np.clip(delta_draw_order, -10, 10) / 10.0
    else:
        delta_draw_order = np.zeros(E, dtype=np.float32)

    draw_order_feature = delta_draw_order.reshape(-1, 1)
    edge_features = np.concatenate([edge_features, draw_order_feature], axis=1)
    sce = compute_sce_edge_features_18(node_bboxes, edge_index)
    edge_features = np.concatenate([edge_features, sce], axis=1)
    return edge_features


def get_sce_edge_feature_names() -> List[str]:
    """Names for SCE 18-d edge features (see compute_sce_edge_features_18, docs/EDGE_FEATURES.md)."""
    return [
        "sce_src_tgt_dx_w1", "sce_src_tgt_dy_h1", "sce_tgt_src_dx_w2", "sce_tgt_src_dy_h2",
        "sce_log_w1_w2", "sce_log_h1_h2",
        "sce_src_left_r", "sce_src_top_r", "sce_r_left_src", "sce_r_top_src",
        "sce_log_w1_rw", "sce_log_h1_rh",
        "sce_tgt_left_r", "sce_tgt_top_r", "sce_r_left_tgt", "sce_r_top_tgt",
        "sce_log_w2_rw", "sce_log_h2_rh",
    ]


def get_edge_feature_names() -> List[str]:
    """Names of edge features in compute_edge_features output order (43-d, includes SCE 18)."""
    return [
        "dx", "dy", "gap_x_norm", "gap_y_norm",
        "x_overlap_ratio", "y_overlap_ratio", "log_w_ratio", "log_h_ratio",
        "delta_left", "delta_right", "delta_center_horizontal",
        "delta_top", "delta_bottom", "delta_middle",
        "iou", "ioa_i", "ioa_j",
        "direction_up", "direction_down", "direction_left", "direction_right", "direction_diagonal",
        "font_log_ratio", "font_abs_log_ratio", "delta_draw_order",
    ] + get_sce_edge_feature_names()


def build_graph(
        node_bboxes: List[List[float]],
        page_width: float,
        page_height: float,
        k_nearest: int = 6,
        alignment_tolerance: float = 3.0,
        max_gap_distance: float = 500.0,
        use_alignment_edges: bool = False,
        node_font_sizes: Optional[List[float]] = None,
        node_draw_orders: Optional[List[int]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    node_bboxes_arr = np.array(node_bboxes, dtype=np.float32)
    N = node_bboxes_arr.shape[0]

    if N == 0:
        return (
            np.array([[], []], dtype=np.int64),
            np.zeros((0, 43), dtype=np.float32),
            np.array([], dtype=np.int64),
        )

    if N == 1:
        return (
            np.array([[0], [0]], dtype=np.int64),
            np.zeros((1, 43), dtype=np.float32),
            np.array([4], dtype=np.int64),
        )

    all_edges_dict = {}
    all_edges_list = []

    nn_edges, nn_directions = find_directional_neighbors(node_bboxes_arr, max_gap_distance)
    if nn_edges.shape[1] > 0:
        for e in range(nn_edges.shape[1]):
            i, j = int(nn_edges[0, e]), int(nn_edges[1, e])
            edge_key = (i, j)
            if edge_key not in all_edges_dict:
                all_edges_dict[edge_key] = int(nn_directions[e])
                all_edges_list.append([i, j])

    knn_edges = find_knn_edges(node_bboxes_arr, k_nearest)
    if knn_edges.shape[1] > 0:
        for e in range(knn_edges.shape[1]):
            i, j = int(knn_edges[0, e]), int(knn_edges[1, e])
            edge_key = (i, j)
            if edge_key not in all_edges_dict:
                all_edges_dict[edge_key] = 4
                all_edges_list.append([i, j])

    if use_alignment_edges:
        max_alignment_distance = np.sqrt(page_width ** 2 + page_height ** 2) * 0.5
        align_edges = find_alignment_edges(
            node_bboxes_arr,
            alignment_tolerance,
            max_distance=max_alignment_distance,
            page_width=page_width,
            page_height=page_height,
        )
        if align_edges.shape[1] > 0:
            for e in range(align_edges.shape[1]):
                i, j = int(align_edges[0, e]), int(align_edges[1, e])
                edge_key = (i, j)
                if edge_key not in all_edges_dict:
                    all_edges_dict[edge_key] = 4
                    all_edges_list.append([i, j])

    if len(all_edges_list) == 0:
        if N <= 10:
            for i in range(N):
                for j in range(N):
                    if i != j:
                        edge_key = (i, j)
                        if edge_key not in all_edges_dict:
                            all_edges_dict[edge_key] = 4
                            all_edges_list.append([i, j])
        else:
            knn_edges = find_knn_edges(node_bboxes_arr, min(k_nearest, N - 1))
            if knn_edges.shape[1] > 0:
                for e in range(knn_edges.shape[1]):
                    i, j = int(knn_edges[0, e]), int(knn_edges[1, e])
                    edge_key = (i, j)
                    if edge_key not in all_edges_dict:
                        all_edges_dict[edge_key] = 4
                        all_edges_list.append([i, j])

    all_edges = all_edges_list
    all_directions = [all_edges_dict[(i, j)] for i, j in all_edges]

    edge_index = np.array(all_edges, dtype=np.int64).T
    edge_directions = np.array(all_directions, dtype=np.int64)

    node_font_sizes_arr = np.array(node_font_sizes, dtype=np.float32) if node_font_sizes is not None else None
    node_draw_orders_arr = np.array(node_draw_orders, dtype=np.float32) if node_draw_orders is not None else None

    edge_features = compute_edge_features(
        node_bboxes_arr,
        edge_index,
        page_width,
        page_height,
        edge_directions=edge_directions,
        node_font_sizes=node_font_sizes_arr,
        node_draw_orders=node_draw_orders_arr,
    )

    return edge_index, edge_features, edge_directions
