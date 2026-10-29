"""
Fast AI Person Segmentation wrapper using MediaPipe Tasks (Selfie Segmenter).
"""

import os
import sys
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def resolve_model_path(model_path: str) -> str:
    if os.path.isabs(model_path) and os.path.exists(model_path):
        return model_path

    # Check PyInstaller bundle folder first
    if hasattr(sys, "_MEIPASS"):
        bundle_p = os.path.join(sys._MEIPASS, os.path.basename(model_path))
        if os.path.exists(bundle_p):
            return bundle_p

    possible_paths = [
        os.path.abspath(model_path),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), model_path),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), model_path),
        os.path.join(os.getcwd(), model_path),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return model_path


class PersonSegmenter:
    def __init__(self, model_path: str = "selfie_segmenter.tflite"):
        model_path = resolve_model_path(model_path)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_confidence_masks=True,
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)

    def get_mask(self, bgr_frame: np.ndarray, feather: bool = True) -> np.ndarray:
        """Returns float32 mask (0.0 to 1.0) with edge smoothing."""
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.segmenter.segment(mp_image)

        confidence_mask = result.confidence_masks[0].numpy_view()
        if len(confidence_mask.shape) == 3:
            mask = confidence_mask[:, :, 0]
        else:
            mask = confidence_mask

        if feather:
            mask = cv2.GaussianBlur(mask, (7, 7), 0)

        return mask
