"""
Youngmin's Features (YF) extraction
Maintained by: AI Researchers
Purpose: Spatial feature maps from PDF page layout analysis
"""

import re
import math
import numpy as np
from collections import Counter, defaultdict

from .common_util import resize_image
from .roi_pooling import extract_bbox_features_by_roi_pooling


def create_pdf_information(page_dict):
    """Create statistical and structural information from PDF page for YF features."""
    info_list = []
    tolerance = 3.0
    width_threshold_ratio = 0.25
    num_threshold_ratio = 0.2
    page_width = page_dict['width']
    list_prefix_pattern = re.compile(r'^(\d+[\.\)]|\(\d+\)|[a-zA-Z][\.\)]|\([a-zA-Z]\)|[-■●])')

    all_raw_data = []
    x1_coords, y1_coords = [], []
    widths, heights = [], []
    font_counts = Counter()

    seen_bboxes = set()
    for block in page_dict["blocks"]:
        if block["type"] != 0: continue
        for line in block["lines"]:
            x1, y1, x2, y2 = line['bbox']

            bbox_key = (int(x1), int(y1), int(x2), int(y2))
            if bbox_key in seen_bboxes:
                continue
            seen_bboxes.add(bbox_key)

            w, h = round(x2 - x1, 1), round(y2 - y1, 1)

            full_text = " ".join([span['text'] for span in line['spans']])
            clean_text = "".join(full_text.split())
            text_len = len(clean_text)

            if text_len > 0:
                num_count = len(re.findall(r'\d', clean_text))
                current_num_ratio = num_count / text_len

                is_noise_for_mode = (current_num_ratio > 0.8) or (current_num_ratio < 0.2 and text_len <= 3)

                if not is_noise_for_mode:
                    widths.append(w)
                    heights.append(h)

            x1_coords.append(x1)
            y1_coords.append(y1)
            if line['spans']:
                font_counts[line['spans'][0]['font']] += 1
                all_raw_data.append((line, line['spans'][0]['font']))

    # Global baseline setup
    indent_baseline = Counter([round(x / tolerance) * tolerance for x in x1_coords]).most_common(1)[0][
        0] if x1_coords else 0
    mode_w = Counter(widths).most_common(1)[0][0] if widths else 1.0
    mode_h = Counter(heights).most_common(1)[0][0] if heights else 1.0
    sorted_fonts = [f[0] for f in font_counts.most_common()]
    font_to_rank = {font: i for i, font in enumerate(sorted_fonts)}
    max_font_rank = len(sorted_fonts) - 1

    def count_within_tolerance(target, coord_list, tol):
        return sum(1 for c in coord_list if abs(c - target) <= tol)

    # Row Context Pre-Analysis
    y_groups = defaultdict(list)
    for line, font in all_raw_data:
        y1 = line['bbox'][1]
        found = False
        for ref_y in y_groups.keys():
            if abs(ref_y - y1) <= tolerance:
                y_groups[ref_y].append(line)
                found = True
                break
        if not found: y_groups[y1].append(line)

    # Feature Calculation
    for line, font in all_raw_data:
        x1, y1, x2, y2 = line['bbox']
        w, h = x2 - x1, y2 - y1
        full_text = " ".join([span['text'] for span in line['spans']])
        clean_text = "".join(full_text.split())
        len_full, len_clean = len(full_text), len(clean_text)

        num_ratio = len(re.findall(r'\d', clean_text)) / len_clean if len_clean > 0 else 0.0
        ws_ratio = ((len_full - len_clean) / len_full) * 2 if len_full > 0 else 0.0
        is_list = list_prefix_pattern.match(full_text.strip())

        row_items = next(items for ref_y, items in y_groups.items() if abs(ref_y - y1) <= tolerance)
        row_count = len(row_items)
        has_strong_anchor = any(len(re.findall(r'\d', "".join(" ".join([s['text'] for s in l['spans']]).split()))) /
                                max(1, len("".join(" ".join([s['text'] for s in l['spans']]).split()))) > 0.8
                                for l in row_items)

        is_grid_candidate = 1.0 if (
                (w / page_width) <= width_threshold_ratio and not is_list and
                (num_ratio >= num_threshold_ratio or (row_count >= 3 and has_strong_anchor))
        ) else 0.0

        h_grid_density = min((row_count - 1) * 0.33 * is_grid_candidate * (1 - ws_ratio) * num_ratio,
                             1.0) if row_count >= 2 else 0.0

        v_l = count_within_tolerance(x1, [l['bbox'][0] for l, f in all_raw_data], tolerance)
        v_r = count_within_tolerance(x2, [l['bbox'][2] for l, f in all_raw_data], tolerance)
        v_grid_density = min((max(v_l, v_r) / 5.0) * is_grid_candidate * (1 - ws_ratio) * num_ratio, 1.0) if max(v_l,
                                                                                                                 v_r) >= 3 else 0.0

        text_density = 1 - num_ratio

        def get_centered_feature(val, mode_val):
            if mode_val <= 0:
                return 0.5
            safe_val = max(val, 0.001)
            ratio = safe_val / mode_val
            diff_log = math.log2(ratio)
            return 1.0 / (1.0 + math.exp(-diff_log))

        w_diff_distance = get_centered_feature(w, mode_w)
        h_diff_distance = get_centered_feature(h, mode_h)

        symbols_count = sum(1 for char in clean_text if not char.isalnum() and char not in [',', '.'])
        sym_ratio = symbols_count / len(full_text)

        info_list.append({
            'bbox': [x1, y1, x2, y2],
            'text': [span['text'] for span in line['spans']],
            'num_ratio': num_ratio,
            'sym_ratio': sym_ratio,
            'start_list_prefix': 1.0 if is_list else 0.0,
            'font_distance': font_to_rank[font] / max_font_rank if max_font_rank > 0 else 0.0,
            'horizontal_grid_density': h_grid_density,
            'vertical_grid_density': v_grid_density,
            'width_diff_distance': w_diff_distance,
            'height_diff_distance': h_diff_distance,
            'whitespace_ratio': ws_ratio,
            'line_indent_degree': min(abs(x1 - indent_baseline) / page_width, 1.0) * (1.0 - num_ratio),
            'text_density': text_density
        })

    return info_list


def create_feature_map(page_img, page, fet_names, info_list, fmap_width=300, fmap_height=300):
    """Create multi-channel spatial feature map for YF features."""
    import cv2

    original_h, original_w = page_img.shape[0], page_img.shape[1]

    scale_w = fmap_width / original_w
    scale_h = fmap_height / original_h

    page_img_scaled = resize_image(page_img, (fmap_width, fmap_height))

    info_list_scaled = []
    for info in info_list:
        info_scaled = info.copy()
        bbox = info['bbox']
        info_scaled['bbox'] = [
            bbox[0] * scale_w,
            bbox[1] * scale_h,
            bbox[2] * scale_w,
            bbox[3] * scale_h
        ]
        info_list_scaled.append(info_scaled)

    page_h, page_w = fmap_height, fmap_width
    num_channels = len(fet_names)
    feature_map = np.zeros((num_channels, page_h, page_w), dtype=np.float32)

    NON_ACCUMULATIVE_FEATURES = {
        'start_list_prefix', 'font_distance', 'width_diff_distance',
        'height_diff_distance', 'line_indent_degree', 'num_ratio',
    }

    ACCUMULATIVE_FEATURES = {
        'horizontal_grid_density', 'vertical_grid_density',
        'text_density', 'image_density'
    }

    gray = cv2.cvtColor(page_img_scaled, cv2.COLOR_BGR2GRAY) if len(page_img_scaled.shape) == 3 else page_img_scaled

    if 'image_density' in fet_names:
        idx = fet_names.index('image_density')
        img_bboxes = [itm["bbox"] for itm in page.get_image_info()]
        for rect in img_bboxes:
            x1 = int(rect[0] * scale_w)
            y1 = int(rect[1] * scale_h)
            x2 = int(rect[2] * scale_w)
            y2 = int(rect[3] * scale_h)

            x1, x2 = max(0, x1), min(page_w, x2)
            y1, y2 = max(0, y1), min(page_h, y2)

            min_size = int(20 * min(scale_w, scale_h))
            if (x2 - x1) >= min_size and (y2 - y1) >= min_size:
                feature_map[idx, y1:y2, x1:x2] = 1.0

        kw = int(page_w * 0.3) | 1
        kh = int(page_h * 0.3) | 1
        feature_map[idx] = cv2.GaussianBlur(feature_map[idx], (kw, kh), 0)

        max_val = feature_map[idx].max()
        if max_val > 0:
            feature_map[idx] /= max_val

    img_density_field = feature_map[fet_names.index('image_density')] if 'image_density' in fet_names else None

    if 'horizontal_line_diffusion' in fet_names:
        idx = fet_names.index('horizontal_line_diffusion')
        grad_y = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3))

        if img_density_field is not None:
            grad_y = grad_y * (1.0 - 0.8 * img_density_field)

        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(page_w * 0.3), 1))
        h_line_mask = cv2.morphologyEx(grad_y, cv2.MORPH_OPEN, h_kernel)
        row_max = np.max(h_line_mask, axis=1)

        threshold = 50 * min(scale_w, scale_h)
        for y in range(page_h):
            if row_max[y] > threshold:
                feature_map[idx, y, :] = 1.0

        kh = int(page_h * 0.3) | 1
        feature_map[idx] = cv2.GaussianBlur(feature_map[idx], (1, kh), sigmaX=0, sigmaY=0)
        if feature_map[idx].max() > 0:
            feature_map[idx] /= feature_map[idx].max()

    if 'vertical_line_diffusion' in fet_names:
        idx = fet_names.index('vertical_line_diffusion')
        grad_x = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3))

        if img_density_field is not None:
            grad_x = grad_x * (1.0 - 0.8 * img_density_field)

        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(page_h * 0.1)))
        v_line_mask = cv2.morphologyEx(grad_x, cv2.MORPH_OPEN, v_kernel)
        col_max = np.max(v_line_mask, axis=0)

        threshold = 50 * min(scale_w, scale_h)
        for x in range(page_w):
            if col_max[x] > threshold:
                feature_map[idx, :, x] = 1.0

        kw = int(page_w * 0.4) | 1
        feature_map[idx] = cv2.GaussianBlur(feature_map[idx], (kw, 1), sigmaX=kw / 6.0, sigmaY=0)
        if feature_map[idx].max() > 0:
            feature_map[idx] /= feature_map[idx].max()

    h_line_field = feature_map[
        fet_names.index('horizontal_line_diffusion')] if 'horizontal_line_diffusion' in fet_names else None

    for info in info_list_scaled:
        x1, y1, x2, y2 = map(int, info['bbox'])
        x1, x2 = max(0, x1), min(page_w, x2)
        y1, y2 = max(0, y1), min(page_h, y2)

        for ch_idx, name in enumerate(fet_names):
            if name in ['column_degree', 'horizontal_line_diffusion', 'vertical_line_diffusion', 'image_density']:
                continue

            val = info[name]

            if name == 'horizontal_grid_density':
                line_proximity = 0
                if h_line_field is not None:
                    roi = h_line_field[y1:y2, x1:x2]
                    if roi.size > 0:
                        line_proximity = np.mean(roi)
                    else:
                        line_proximity = 0
                if val > 0:
                    boost = 1.0 + 0.8 * line_proximity
                    val = min(val * boost, 1.0)

            if name == 'num_ratio' and img_density_field is not None:
                roi = img_density_field[y1:y2, x1:x2]
                if roi.size > 0:
                    img_influence = np.mean(roi)
                else:
                    img_influence = 0.0

                supp = np.exp(-3.0 * img_influence)
                val *= supp

            if val <= 0: continue

            roi = feature_map[ch_idx, y1:y2, x1:x2]

            if name in NON_ACCUMULATIVE_FEATURES:
                roi = np.maximum(roi, val)
            elif name in ACCUMULATIVE_FEATURES:
                roi = np.clip(roi + val, 0.0, 1.0)
            else:
                roi = np.clip(roi + val, 0.0, 1.0)

            feature_map[ch_idx, y1:y2, x1:x2] = roi

    if 'column_degree' in fet_names:
        idx = fet_names.index('column_degree')
        total_bboxes = len(info_list_scaled)

        boundaries = [0]

        if total_bboxes > 0:
            filtered_coords = [round(i['bbox'][0], 0) for i in info_list_scaled if i.get('num_ratio', 0.0) <= 0.2]
            filtered_coords += [round(i['bbox'][2], 0) for i in info_list_scaled if i.get('num_ratio', 0.0) <= 0.2]

            if filtered_coords:
                coord_counts = Counter(filtered_coords)
                threshold = total_bboxes * 0.25
                found_boundaries = sorted([x for x, c in coord_counts.items() if c > threshold])
                boundaries = sorted(list(set([0] + found_boundaries)))

            extended = boundaries + [page_w]
            for i in range(len(extended) - 1):
                degree_val = min((i + 1) / 40.0, 1.0)
                feature_map[idx, :, int(extended[i]):int(extended[i + 1])] = degree_val

            if 'line_indent_degree' in fet_names:
                li_idx = fet_names.index('line_indent_degree')
                for info in info_list_scaled:
                    x1, y1, x2, y2 = map(int, info['bbox'])

                    insert_idx = np.searchsorted(boundaries, x1 + 5.0)
                    b_idx = max(0, insert_idx - 1)
                    local_baseline = boundaries[b_idx]

                    indent_dist = abs(x1 - local_baseline)
                    raw_indent_degree = min(indent_dist / page_w, 1.0)

                    num_ratio = info.get('num_ratio', 0.0)
                    line_indent_degree = raw_indent_degree * (1.0 - num_ratio)

                    x1_f, x2_f = max(0, x1), min(page_w, x2)
                    y1_f, y2_f = max(0, y1), min(page_h, y2)
                    feature_map[li_idx, y1_f:y2_f, x1_f:x2_f] = line_indent_degree

    for name, kw_ratio, kh_ratio in [
        ('text_density', 0.1, 0.1),
        ('vertical_grid_density', 0.05, 0.4),
        ('horizontal_grid_density', 0.5, 0.05),
    ]:
        if name in fet_names:
            idx = fet_names.index(name)
            kw, kh = int(page_w * kw_ratio) | 1, int(page_h * kh_ratio) | 1
            feature_map[idx] = cv2.GaussianBlur(feature_map[idx], (kw, kh), sigmaX=0, sigmaY=0)

            max_val = feature_map[idx].max()
            if max_val > 0:
                feature_map[idx] /= max_val

    return feature_map


def extract_yf_features(data_dict, page, page_dict, return_fet_map=False):
    """Extract Youngmin's Features (YF) - spatial feature maps."""
    fet_names = [
        'num_ratio', 'start_list_prefix', 'font_distance', 'text_density',
        'horizontal_grid_density', 'vertical_grid_density', 'width_diff_distance',
        'whitespace_ratio', 'height_diff_distance', 'sym_ratio', 'column_degree',
        'horizontal_line_diffusion', 'vertical_line_diffusion', 'line_indent_degree',
        'image_density',
    ]

    page_img = data_dict['image']
    page_h, page_w = page_img.shape[0], page_img.shape[1]

    pdf_info = create_pdf_information(page_dict)
    feature_map = create_feature_map(page_img, page, info_list=pdf_info, fet_names=fet_names)

    if return_fet_map:
        return feature_map

    original_bboxes = data_dict['bboxes']

    margin = 50
    expanded_bboxes = []
    for bbox in original_bboxes:
        x1, y1, x2, y2 = bbox
        ex1 = max(0, x1 - margin)
        ey1 = max(0, y1 - margin)
        ex2 = min(page_w, x2 + margin)
        ey2 = min(page_h, y2 + margin)
        expanded_bboxes.append([ex1, ey1, ex2, ey2])

    yf_features_orig = extract_bbox_features_by_roi_pooling(
        feature_map[None, ...],
        original_bboxes,
        page_w,
        page_h,
        apply_softmax=False,
        concat_mean_max=False,
        add_uncertainty=False
    )

    yf_features_exp = extract_bbox_features_by_roi_pooling(
        feature_map[None, ...],
        expanded_bboxes,
        page_w,
        page_h,
        apply_softmax=False,
        concat_mean_max=False,
        add_uncertainty=False
    )

    for i, custom_feature in enumerate(data_dict['custom_features']):
        orig_vector = yf_features_orig[i]
        exp_vector = yf_features_exp[i]

        for f_idx, f_name in enumerate(fet_names):
            if f_name in ['num_ratio', 'sym_ratio'] or f_name.endswith('_density') or f_name.endswith('_diffusion'):
                val = float(exp_vector[f_idx])
            else:
                val = float(orig_vector[f_idx])
            custom_feature['yf_' + f_name] = val

    return data_dict
