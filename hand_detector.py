"""
Visual Hand Gesture & Snap Detector using MediaPipe Hand Landmarker.
Detects when the user holds up their hand and performs a snap gesture (Thumb + Middle finger pinch-and-release).
"""

import os
import time
import math
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandSnapDetector:
    def __init__(self, model_path: str = "hand_landmarker.task"):
        if not os.path.isabs(model_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Hand model not found at: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        # State tracking for pinch-and-snap gesture
        self.hand_visible = False
        self.last_pinch_time = 0.0
        self.was_pinching = False
        self.snapped = False
        self.cooldown_sec = 2.5
        self.last_snap_time = 0.0

    def process(self, bgr_frame: np.ndarray):
        """
        Processes camera frame to detect hands and snap motion.
        Returns: (hand_visible: bool, visual_snap_detected: bool, hand_landmarks)
        """
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.detector.detect(mp_image)

        now = time.time()
        self.hand_visible = len(result.hand_landmarks) > 0
        visual_snap = False

        if self.hand_visible:
            for landmarks in result.hand_landmarks:
                # Landmark 4: Thumb tip
                # Landmark 8: Index tip
                # Landmark 12: Middle finger tip
                # Landmark 0: Wrist
                thumb = landmarks[4]
                index = landmarks[8]
                middle = landmarks[12]
                wrist = landmarks[0]

                # Calculate Euclidean distance between thumb and middle/index finger in normalized coords
                dist_thumb_middle = math.hypot(thumb.x - middle.x, thumb.y - middle.y)
                dist_thumb_index = math.hypot(thumb.x - index.x, thumb.y - index.y)
                min_dist = min(dist_thumb_middle, dist_thumb_index)

                # Hand scale (distance from wrist to middle tip)
                hand_scale = math.hypot(middle.x - wrist.x, middle.y - wrist.y) + 1e-4
                normalized_dist = min_dist / hand_scale

                # Pinch state (fingers touching for snap preparation)
                is_pinching = normalized_dist < 0.22

                if is_pinching:
                    self.was_pinching = True
                    self.last_pinch_time = now
                elif self.was_pinching:
                    # Released! If release happened within 0.05 to 0.4 seconds of pinch -> SNAP!
                    dt = now - self.last_pinch_time
                    if 0.04 < dt < 0.45 and (now - self.last_snap_time) > self.cooldown_sec:
                        visual_snap = True
                        self.last_snap_time = now
                    self.was_pinching = False

        return self.hand_visible, visual_snap, result.hand_landmarks

    def check_snap(self) -> bool:
        if self.snapped:
            self.snapped = False
            return True
        return False
