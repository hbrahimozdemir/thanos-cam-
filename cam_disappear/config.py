"""
Configuration system for Thanos Disappear Camera.
Supports persistent JSON settings and CLI overrides.
"""

import json
import os
from dataclasses import dataclass, asdict, field


@dataclass
class AppConfig:
    # Camera settings
    camera_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    mirror_camera: bool = True

    # Trigger settings
    # Modes: "hybrid" (Strict Gesture + Audio), "gesture" (Hand Snap only), "audio" (Snap Sound only), "hotkey" (Space/S key only)
    trigger_mode: str = "hybrid"
    audio_threshold: float = 0.035
    min_arm_duration_sec: float = 0.20   # Must hold snap pinch for 0.2s before releasing to prevent speech/gesture false triggers
    sync_window_sec: float = 0.20        # Audio click and gesture release must coincide within 0.2s
    trigger_cooldown_sec: float = 3.0

    # Effect settings
    dissolve_duration_sec: float = 2.4
    particle_count_multiplier: float = 1.0
    wind_direction: str = "top_right"    # "top_right", "top_left", "up"
    enable_embers: bool = True           # Glowing hot sparks along dissolve edge
    enable_charred_edge: bool = True     # Burn/char effect at dissolve boundary

    # File paths
    background_path: str = "background.jpg"
    model_segmenter_path: str = "selfie_segmenter.tflite"
    model_hand_path: str = "hand_landmarker.task"

    def save(self, filepath: str = "config.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4)

    @classmethod
    def load(cls, filepath: str = "config.json") -> "AppConfig":
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f"[Config] Warning: Failed to parse {filepath} ({e}), using defaults.")
        return cls()
