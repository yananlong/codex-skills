"""
Image Model Features (IMF) extraction
Maintained by: AI Researchers
Purpose: Extract image-based features using neural network (ONNX)
"""

import numpy as np

from .common_util import resize_image, to_gray, extract_bboxes_from_segmentation
from .pymupdf_util_base import BOX_IMAGE


def image_feature_extraction_task(page_img, feature_extractor, input_type, aug_fetmap = None):
    """Extract image-based features using neural network."""
    page_h, page_w, _ = page_img.shape

    input_shape = feature_extractor.get_inputs()[0].shape
    target_height = input_shape[2]
    target_width = input_shape[3]

    img_resized = resize_image(page_img, (target_width, target_height))
    img_gray = to_gray(img_resized)

    img_gray = img_gray.astype(np.float32)
    min_val, max_val = img_gray.min(), img_gray.max()
    if max_val > min_val:
        img_gray = (img_gray - min_val) / (max_val - min_val)
    else:
        img_gray = np.zeros_like(img_gray, dtype=np.float32)

    nn_input = img_gray.astype(np.float32)
    nn_input = np.expand_dims(nn_input, axis=0)
    if aug_fetmap is not None:
        nn_input = np.concatenate([nn_input, aug_fetmap], axis=0)
    nn_input = np.expand_dims(nn_input, axis=0)

    ort_inputs = {feature_extractor.get_inputs()[0].name: nn_input}
    ort_outputs = feature_extractor.run(None, ort_inputs)[0]

    feature_map = ort_outputs
    bboxes_to_add = []
    box_types_to_add = []

    if 'seg-image' in input_type:
        class_names = ['background', 'text', 'title', 'picture', 'table', 'list-item', 'page-header', 'page-footer',
                       'section-header', 'footnote', 'caption', 'formula']

        prior_det = extract_bboxes_from_segmentation(ort_outputs, class_names=class_names,
                                                     target_class=['picture'],
                                                     min_component_area=50, morphology_kernel_size=3)
        resize_x = page_w / target_width
        resize_y = page_h / target_height
        for det in prior_det:
            if det['class'] == 'picture' and det['score'] > 0.8:
                bbox = [
                    det['bbox'][0] * resize_x, det['bbox'][1] * resize_y,
                    det['bbox'][2] * resize_x, det['bbox'][3] * resize_y
                ]
                bboxes_to_add.append(bbox)
                box_types_to_add.append(BOX_IMAGE)

    return feature_map, bboxes_to_add, box_types_to_add
