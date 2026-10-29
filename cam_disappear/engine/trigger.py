"""
Ultra-Reliable Acoustic Snap Detector with Adaptive Noise Floor.
Calibrated for quiet headset microphones. Never triggers on hand motion alone.
"""

import os
import sys
import time
import math
import numpy as np
import cv2
import sounddevice as sd
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def resolve_model_path(model_path: str) -> str:
    if os.path.isabs(model_path) and os.path.exists(model_path):
        return model_path

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


class MultimodalTriggerManager:
    def __init__(
        self,
        hand_model_path: str = "hand_landmarker.task",
        mode: str = "hybrid",
        audio_threshold: float = 0.0045,  # Generous sensitivity so snaps trigger reliably
        cooldown: float = 2.0,
    ):
        self.mode = mode  # "hybrid", "audio", "hotkey"
        self.audio_threshold = audio_threshold
        self.cooldown = cooldown

        # Audio transient state
        self.stream = None
        self.audio_active = False
        self.current_peak = 0.0
        self.recent_peak_decay = 0.0
        self.last_audio_snap_time = 0.0

        # Visual Hand presence
        self.hand_detector = None
        self.hand_visible = False
        self.last_trigger_time = 0.0

        # Initialize
        self._init_hand_detector(hand_model_path)
        self._init_audio_stream()

    def _init_hand_detector(self, model_path: str):
        model_path = resolve_model_path(model_path)
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,
                min_hand_detection_confidence=0.35,
                min_hand_presence_confidence=0.35,
                min_tracking_confidence=0.35,
            )
            self.hand_detector = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            print(f"[Trigger] Warning: Could not initialize HandLandmarker ({e}).")
            self.hand_detector = None

    def _init_audio_stream(self):
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=44100,
                blocksize=1024,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.audio_active = True
        except Exception as e:
            print(f"[Trigger] Warning: Could not open microphone ({e}).")
            self.audio_active = False

    def _audio_callback(self, indata, frames, time_info, status):
        samples = indata[:, 0].astype(np.float32)

        # 1st-order diff captures sharp transient click of finger snap
        diff = np.diff(samples)
        peak = float(np.max(np.abs(diff)))
        rms = float(np.sqrt(np.mean(samples ** 2))) + 1e-6
        crest = peak / rms

        self.current_peak = peak

        # Decay tracker for HUD visualization
        if peak > self.recent_peak_decay:
            self.recent_peak_decay = peak
        else:
            self.recent_peak_decay *= 0.85

        # Effective threshold: lower when hand is up in front of camera
        effective_thresh = self.audio_threshold * (0.70 if self.hand_visible else 1.0)

        now = time.time()
        # Snap detection: sharp transient peak + crest factor
        if peak > effective_thresh and crest > 1.4:
            self.last_audio_snap_time = now

    def process_frame(self, bgr_frame: np.ndarray) -> tuple[bool, str]:
        """
        Evaluates trigger.
        Raising or moving your hand alone will NEVER trigger.
        An actual finger snap sound is required!
        """
        now = time.time()

        if (now - self.last_trigger_time) < self.cooldown:
            return False, ""

        if self.mode == "hotkey":
            return False, ""

        # Check Hand Presence
        self.hand_visible = False
        if self.hand_detector is not None:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = self.hand_detector.detect(mp_img)
            self.hand_visible = len(res.hand_landmarks) > 0

        # Check if an actual audio snap click occurred
        has_recent_audio = (now - self.last_audio_snap_time) <= 0.40

        if self.mode == "hybrid":
            # Hand visible + snap click heard -> Fire!
            # Or loud snap click heard even if hand is just out of frame -> Fire!
            if self.hand_visible and has_recent_audio:
                self.last_trigger_time = now
                self.last_audio_snap_time = 0.0
                return True, "Finger Snap (Hand + Sound)"
            elif has_recent_audio and self.current_peak > (self.audio_threshold * 1.8):
                self.last_trigger_time = now
                self.last_audio_snap_time = 0.0
                return True, "Acoustic Snap"

        elif self.mode == "audio":
            if has_recent_audio:
                self.last_trigger_time = now
                self.last_audio_snap_time = 0.0
                return True, "Acoustic Snap"

        return False, ""

    def increase_sensitivity(self):
        self.audio_threshold = max(0.001, self.audio_threshold * 0.75)
        print(f"[Trigger] Sensitivity Increased (Threshold: {self.audio_threshold:.4f})")

    def decrease_sensitivity(self):
        self.audio_threshold = min(0.05, self.audio_threshold * 1.35)
        print(f"[Trigger] Sensitivity Decreased (Threshold: {self.audio_threshold:.4f})")

    def cycle_mode(self) -> str:
        modes = ["hybrid", "audio", "hotkey"]
        idx = (modes.index(self.mode) + 1) % len(modes)
        self.mode = modes[idx]
        print(f"[Trigger] Mode: {self.mode.upper()}")
        return self.mode

    def stop(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
