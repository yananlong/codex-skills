"""
Adaptive RoI-pooling feature extraction.

Automatically dispatches between:
  - Naive per-bbox loop: zero setup cost, best for small B
  - SAT (integral image) path: O(C*H*W) setup, O(1) per-bbox mean query,
    best for large B

Calibrated for ~300x300 feature maps with C~10.

Crossover points (B * avg_patch_area / H*W):
  - uncertainty=True:  ~2.0   (SAT setup amortized across entropy/margin maps)
  - uncertainty=False: ~50.0  (naive loop is extremely fast without probs)
"""

import numpy as np
from typing import List, Tuple
from collections import defaultdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _softmax_channels(fmap: np.ndarray) -> np.ndarray:
    """Channel-wise softmax along axis=0 of a (C, H, W) tensor."""
    C, H, W = fmap.shape
    f = fmap.reshape(C, -1).copy()
    f -= f.max(axis=0, keepdims=True)
    np.exp(f, out=f)
    f /= f.sum(axis=0, keepdims=True) + 1e-12
    return f.reshape(C, H, W)


def _build_sat(arr: np.ndarray) -> np.ndarray:
    """Summed Area Table over the last two axes. Returns (..., H+1, W+1)."""
    prefix = arr.shape[:-2]
    H, W = arr.shape[-2], arr.shape[-1]
    sat = np.zeros((*prefix, H + 1, W + 1), dtype=np.float64)
    np.cumsum(arr, axis=-2, out=sat[..., 1:, 1:])
    np.cumsum(sat[..., 1:, 1:], axis=-1, out=sat[..., 1:, 1:])
    return sat


def _sat_rect_sum(sat, y1, x1, y2, x2):
    """Vectorized rectangle sum on a SAT. Coords are inclusive."""
    return (
        sat[..., y2 + 1, x2 + 1]
        - sat[..., y1, x2 + 1]
        - sat[..., y2 + 1, x1]
        + sat[..., y1, x1]
    )


def _grid_coords_vec(bb, W, H, page_width, page_height):
    """Map image-space bboxes to feature-grid indices (vectorized)."""
    sx = W / float(page_width)
    sy = H / float(page_height)
    gx1 = np.floor(bb[:, 0] * sx).astype(np.intp).clip(0, W - 1)
    gy1 = np.floor(bb[:, 1] * sy).astype(np.intp).clip(0, H - 1)
    gx2 = (np.ceil(bb[:, 2] * sx).astype(np.intp) - 1).clip(0, W - 1)
    gy2 = (np.ceil(bb[:, 3] * sy).astype(np.intp) - 1).clip(0, H - 1)
    gx2 = np.maximum(gx2, gx1)
    gy2 = np.maximum(gy2, gy1)
    return gx1, gy1, gx2, gy2


# ---------------------------------------------------------------------------
# Path A: naive per-bbox loop (low overhead)
# ---------------------------------------------------------------------------

def _path_naive(fmap_used, probs, gx1, gy1, gx2, gy2,
                concat_mean_max, add_uncertainty):
    C = fmap_used.shape[0]
    B = len(gx1)
    base_dim = C * 2 if concat_mean_max else C
    out_dim = base_dim + (2 if add_uncertainty else 0)
    out = np.zeros((B, out_dim), dtype=np.float32)

    for i in range(B):
        y1i, y2i, x1i, x2i = gy1[i], gy2[i], gx1[i], gx2[i]
        patch = fmap_used[:, y1i:y2i + 1, x1i:x2i + 1]
        if patch.size == 0:
            continue

        mean_vec = patch.mean(axis=(1, 2))
        if concat_mean_max:
            pooled = np.concatenate([mean_vec, patch.max(axis=(1, 2))])
        else:
            pooled = mean_vec

        if add_uncertainty:
            pp = probs[:, y1i:y2i + 1, x1i:x2i + 1]
            eps = 1e-12
            ent = -(pp * np.log(pp + eps)).sum(axis=0).mean()
            Cp = pp.shape[0]
            flat = pp.reshape(Cp, -1)
            if Cp >= 2:
                ip = np.argpartition(flat, -2, axis=0)[-2:]
                t2 = np.take_along_axis(flat, ip, axis=0)
                t2.sort(axis=0)
                margin = (t2[1] - t2[0]).mean()
            else:
                margin = flat[0].mean()
            pooled = np.concatenate([pooled, [ent, margin]])

        out[i, :pooled.shape[0]] = pooled.astype(np.float32)
    return out


# ---------------------------------------------------------------------------
# Path B: SAT-based (amortized O(1) mean + grouped batch max)
# ---------------------------------------------------------------------------

def _path_sat(fmap_used, probs, gx1, gy1, gx2, gy2,
              concat_mean_max, add_uncertainty):
    C, H, W = fmap_used.shape
    B = len(gx1)
    areas = ((gy2 - gy1 + 1) * (gx2 - gx1 + 1)).astype(np.float64)

    # Mean via SAT
    sat_f = _build_sat(fmap_used)  # (C, H+1, W+1)
    mean_all = (_sat_rect_sum(sat_f, gy1, gx1, gy2, gx2)
                / areas[np.newaxis, :]).T.astype(np.float32)  # (B, C)

    # Max via grouped batch slicing
    if concat_mean_max:
        max_all = np.empty((B, C), dtype=np.float32)
        ph_arr = gy2 - gy1 + 1
        pw_arr = gx2 - gx1 + 1
        groups = defaultdict(list)
        for i in range(B):
            groups[(int(ph_arr[i]), int(pw_arr[i]))].append(i)
        for (ph, pw), indices in groups.items():
            idx = np.array(indices, dtype=np.intp)
            n = len(idx)
            patches = np.empty((n, C, ph, pw), dtype=fmap_used.dtype)
            for j, bi in enumerate(idx):
                patches[j] = fmap_used[:, gy1[bi]:gy1[bi]+ph, gx1[bi]:gx1[bi]+pw]
            max_all[idx] = patches.max(axis=(2, 3))

    # Uncertainty via pre-computed maps + SAT
    if add_uncertainty:
        eps = 1e-12
        # Entropy
        ent_map = -(probs * np.log(probs + eps)).sum(axis=0)
        sat_e = _build_sat(ent_map)
        entropy_mean = (_sat_rect_sum(sat_e, gy1, gx1, gy2, gx2)
                        / areas).astype(np.float32)
        # Margin
        if C >= 2:
            t2i = np.argpartition(probs, -2, axis=0)[-2:]
            t2v = np.take_along_axis(probs, t2i, axis=0)
            margin_map = t2v.max(axis=0) - t2v.min(axis=0)
        else:
            margin_map = probs[0]
        sat_m = _build_sat(margin_map)
        margin_mean = (_sat_rect_sum(sat_m, gy1, gx1, gy2, gx2)
                       / areas).astype(np.float32)

    parts = [mean_all]
    if concat_mean_max:
        parts.append(max_all)
    if add_uncertainty:
        parts.append(entropy_mean[:, np.newaxis])
        parts.append(margin_mean[:, np.newaxis])
    return np.concatenate(parts, axis=1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_bbox_features_by_roi_pooling(
    features: np.ndarray,
    bboxes: List[Tuple[float, float, float, float]],
    page_width: int,
    page_height: int,
    apply_softmax: bool = False,
    concat_mean_max: bool = True,
    add_uncertainty: bool = False,
) -> np.ndarray:
    """
    Extract per-bbox features with mean/max pooling and optional uncertainty.

    Adaptively dispatches between naive loop and SAT-based vectorized path
    based on the estimated computational cost ratio.
    """
    assert features.ndim == 4
    N, C, H, W = features.shape
    assert N == 1

    B = len(bboxes)
    if B == 0:
        base_dim = C * 2 if concat_mean_max else C
        return np.zeros((0, base_dim + (2 if add_uncertainty else 0)),
                        dtype=np.float32)

    fmap = features[0]
    bb = np.asarray(bboxes, dtype=np.float64)
    gx1, gy1, gx2, gy2 = _grid_coords_vec(bb, W, H, page_width, page_height)

    # ---- Dispatch heuristic ----
    # Cost metric: B * avg_patch_area / (H * W)
    # Empirically calibrated thresholds for 300x300, C=10:
    #   uncertainty=True  -> crossover at metric ~ 2   (SAT builds 3 tables)
    #   uncertainty=False -> crossover at metric ~ 50  (loop skips probs entirely)
    avg_patch_area = float(((gy2 - gy1 + 1) * (gx2 - gx1 + 1)).mean())
    cost_metric = B * avg_patch_area / float(H * W)
    threshold = 2.0 if add_uncertainty else 50.0

    use_sat = cost_metric > threshold

    if use_sat:
        probs = _softmax_channels(fmap)
        fmap_used = probs if apply_softmax else fmap
        return _path_sat(fmap_used, probs, gx1, gy1, gx2, gy2,
                         concat_mean_max, add_uncertainty)
    else:
        # Lazy computation: skip softmax when not needed
        if apply_softmax:
            fmap_used = _softmax_channels(fmap)
            probs = fmap_used if add_uncertainty else None
        else:
            fmap_used = fmap
            probs = _softmax_channels(fmap) if add_uncertainty else None
        return _path_naive(fmap_used, probs, gx1, gy1, gx2, gy2,
                           concat_mean_max, add_uncertainty)
