"""
Fast Person Segmentation using MediaPipe Tasks (Selfie Segmenter).
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PersonSegmenter:
    def __init__(self, model_path: str = "selfie_segmenter.tflite"):
        if not os.path.isabs(model_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_confidence_masks=True,
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)

    def get_mask(self, bgr_frame: np.ndarray, feather: bool = True) -> np.ndarray:
        """
        Runs segmentation on a BGR camera frame and returns a float32 mask (0.0 to 1.0),
        where 1.0 represents the person and 0.0 represents the background.
        """
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        segmentation_result = self.segmenter.segment(mp_image)

        # confidence_masks[0] is person confidence (float32, 0.0 -> 1.0)
        confidence_mask = segmentation_result.confidence_masks[0].numpy_view()
        
        # Squeeze extra dimension if present (H, W, 1) -> (H, W)
        if len(confidence_mask.shape) == 3:
            mask = confidence_mask[:, :, 0]
        else:
            mask = confidence_mask

        # Apply feathering for buttery-smooth edges (natural hair, edges, shoulders)
        if feather:
            mask = cv2.GaussianBlur(mask, (7, 7), 0)

        return mask
