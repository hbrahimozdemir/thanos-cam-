"""
ThanosCam (CamDisappear) - Standalone Virtual Camera Application.
Disintegrate into dust and vanish from video calls with a snap of your fingers.
"""

import os
import sys
import time
import argparse

# Cross-platform safe terminal encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import cv2
import numpy as np

from cam_disappear.config import AppConfig
from cam_disappear.engine.thanos_effect import ThanosDisintegrationEngine
from cam_disappear.engine.segmenter import PersonSegmenter
from cam_disappear.engine.trigger import MultimodalTriggerManager
from cam_disappear.engine.virtual_cam import VirtualCameraOutput


class CamDisappearApp:
    def __init__(self, config: AppConfig):
        self.config = config

        self.clean_background = None
        self.state = "LIVE"  # "LIVE", "DISINTEGRATING", "DISAPPEARED"
        self.current_cam_idx = self.config.camera_index
        self.cap = None

        # 1. AI Person Segmentation
        print("🧠 [1/4] Loading MediaPipe Person Segmentation...")
        self.segmenter = PersonSegmenter(self.config.model_segmenter_path)

        # 2. Particle Engine
        print("🌪️ [2/4] Initializing Thanos Particle Disintegration Engine...")
        self.effect = ThanosDisintegrationEngine(
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps,
        )

        # 3. Multimodal Trigger
        print("⚡ [3/4] Initializing Snap & Hand Gesture Detector...")
        self.trigger = MultimodalTriggerManager(
            hand_model_path=self.config.model_hand_path,
            mode=self.config.trigger_mode,
            audio_threshold=0.018,
            cooldown=self.config.trigger_cooldown_sec,
        )

        # 4. Virtual Camera
        print("📷 [4/4] Connecting to Virtual Camera Driver...")
        self.vcam = VirtualCameraOutput(
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps,
        )

        self._load_saved_background()

    def _load_saved_background(self):
        if os.path.exists(self.config.background_path):
            img = cv2.imread(self.config.background_path)
            if img is not None:
                self.clean_background = cv2.resize(img, (self.config.width, self.config.height))
                print(f"✅ Loaded cached empty chair background: {self.config.background_path}")

    def capture_background(self, frame: np.ndarray):
        """Saves current camera frame as the empty chair background plate."""
        self.clean_background = frame.copy()
        cv2.imwrite(self.config.background_path, self.clean_background)
        print(f"📸 Empty chair background saved: {self.config.background_path}")

    def trigger_snap(self, frame: np.ndarray, mask: np.ndarray, source: str = "Manual"):
        if self.clean_background is None:
            print("⚠️ WARNING: Step out of frame and press [B] to save your empty chair first!")
            return

        if self.state == "LIVE":
            print(f"💥 SNAP TRIGGERED ({source})! Disintegrating into dust...")
            self.state = "DISINTEGRATING"
            self.effect.start(
                person_frame=frame,
                person_mask=mask,
                background_plate=self.clean_background,
                duration_sec=self.config.dissolve_duration_sec,
                wind_direction=self.config.wind_direction,
            )

    def reset_to_live(self):
        print("✨ Restoring live camera...")
        self.effect.reset()
        self.state = "LIVE"

    def open_camera(self, idx: int):
        """Opens camera with DirectShow backend."""
        if self.cap is not None:
            self.cap.release()

        print(f"🎥 Connecting to Camera {idx}...")
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap = cap
            self.current_cam_idx = idx
            print(f"✅ Camera {idx} connected successfully!")
            return True
        else:
            print(f"❌ Could not open Camera {idx}.")
            return False

    def switch_camera(self):
        """Cycles to the next camera index (0 -> 1 -> 2 -> 0)."""
        next_idx = (self.current_cam_idx + 1) % 4
        print(f"🔄 Switching camera to index {next_idx}...")
        if not self.open_camera(next_idx):
            # If next index fails, try going back to 0
            self.open_camera(0)

    def draw_hud(self, frame: np.ndarray):
        """Draws aesthetic English HUD on local preview window."""
        h, w = frame.shape[:2]

        # Top and bottom bars
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 52), (18, 18, 22), -1)
        cv2.rectangle(overlay, (0, h - 35), (w, h), (18, 18, 22), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # 1. State indicator (Left)
        if self.state == "LIVE":
            st_text = "STATUS: LIVE (Visible)"
            st_color = (0, 230, 100)
        elif self.state == "DISINTEGRATING":
            st_text = f"DISINTEGRATING... (%{int(self.effect.progress * 100)})"
            st_color = (100, 180, 255)
        else:
            st_text = "DISAPPEARED (Chair Empty)"
            st_color = (0, 70, 255)

        cv2.putText(frame, st_text, (15, 25), cv2.FONT_HERSHEY_DUPLEX, 0.52, st_color, 1, cv2.LINE_AA)

        # Sub-status: Mode & Camera
        info_text = f"Mode: {self.trigger.mode.upper()} [T] | Cam: {self.current_cam_idx} [C to switch]"
        cv2.putText(frame, info_text, (15, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 220), 1, cv2.LINE_AA)

        # 2. Hand status (Center)
        if self.trigger.hand_visible:
            hand_str = "HAND: READY TO SNAP"
            hand_col = (0, 255, 120)
        else:
            hand_str = "HAND: Waiting (Raise hand)"
            hand_col = (130, 130, 130)

        cv2.putText(frame, hand_str, (int(w * 0.38), 30), cv2.FONT_HERSHEY_SIMPLEX, 0.44, hand_col, 1, cv2.LINE_AA)

        # 3. Audio meter & threshold marker (Right)
        if self.trigger.audio_active:
            meter_w = 130
            meter_h = 13
            mx = w - meter_w - 15
            my = 12

            cv2.rectangle(frame, (mx, my), (mx + meter_w, my + meter_h), (45, 45, 50), -1)

            # Audio peak level
            peak_val = self.trigger.recent_peak_decay
            fill_w = int(np.clip(peak_val * 1200, 0, meter_w))
            cv2.rectangle(frame, (mx, my), (mx + fill_w, my + meter_h), (0, 220, 255), -1)

            # Red threshold marker
            th = self.trigger.audio_threshold * (0.65 if self.trigger.hand_visible else 1.0)
            th_x = int(np.clip(mx + th * 1200, mx, mx + meter_w))
            cv2.line(frame, (th_x, my - 2), (th_x, my + meter_h + 2), (0, 0, 255), 2)

            cv2.putText(frame, f"Snap Threshold: {th:.3f} (+/-)", (mx, my + meter_h + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (180, 180, 180), 1)

        # 4. Bottom controls bar
        bg_status = "SAVED" if self.clean_background is not None else "EMPTY! (Press B)"
        ctrl = f"[B] Empty Chair: {bg_status} | [S] Snap | [C] Switch Cam | [R] Reset | [+/-] Sensitivity | [Q] Quit"
        cv2.putText(frame, ctrl, (12, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (210, 210, 210), 1, cv2.LINE_AA)

    def run(self):
        if not self.open_camera(self.current_cam_idx):
            print("❌ Error: Could not connect to any camera. Please make sure no other app (Teams/Zoom) is locking it.")
            return

        cv2.namedWindow("ThanosCam (CamDisappear)", cv2.WINDOW_AUTOSIZE)

        print("\n" + "=" * 60)
        print("🚀 THANOSCAM IS READY!")
        print("  [B]        -> Step out and save Empty Chair")
        print("  [S] / Space-> Snap / Disintegrate immediately")
        print("  [C]        -> Switch to next camera device")
        print("  [T]        -> Switch trigger mode (Hybrid/Audio/Gesture/Hotkey)")
        print("  [+] / [-]  -> Adjust snap sensitivity")
        print("  [R]        -> Reset & Reappear")
        print("  [Q] / ESC  -> Quit")
        print("=" * 60 + "\n")

        try:
            while True:
                ret, raw_frame = self.cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                raw_frame = cv2.resize(raw_frame, (self.config.width, self.config.height))
                if self.config.mirror_camera:
                    raw_frame = cv2.flip(raw_frame, 1)

                # Multimodal Trigger Check
                if self.state == "LIVE":
                    triggered, trigger_src = self.trigger.process_frame(raw_frame)
                    if triggered:
                        mask = self.segmenter.get_mask(raw_frame)
                        self.trigger_snap(raw_frame, mask, source=trigger_src)

                # State Rendering
                clean_output_frame = None

                if self.state == "LIVE":
                    clean_output_frame = raw_frame.copy()
                elif self.state == "DISINTEGRATING":
                    disintegrated = self.effect.update()
                    clean_output_frame = disintegrated if disintegrated is not None else self.clean_background.copy()
                    if self.effect.is_finished:
                        self.state = "DISAPPEARED"
                        print("💀 Disintegration complete. Chair is empty.")
                elif self.state == "DISAPPEARED":
                    clean_output_frame = self.clean_background.copy()

                # Stream to Virtual Camera
                self.vcam.send(clean_output_frame)

                # Local Preview Window with HUD
                hud_frame = clean_output_frame.copy()
                self.draw_hud(hud_frame)
                cv2.imshow("ThanosCam (CamDisappear)", hud_frame)

                # Key controls
                key = cv2.waitKey(1) & 0xFF
                if key in [ord("q"), ord("Q"), 27]:
                    break
                elif key in [ord("b"), ord("B")]:
                    self.capture_background(raw_frame)
                elif key in [ord("s"), ord("S"), 32]:  # S or Space
                    mask = self.segmenter.get_mask(raw_frame)
                    self.trigger_snap(raw_frame, mask, source="Hotkey")
                elif key in [ord("c"), ord("C")]:
                    self.switch_camera()
                elif key in [ord("r"), ord("R")]:
                    self.reset_to_live()
                elif key in [ord("t"), ord("T")]:
                    self.trigger.cycle_mode()
                    self.config.trigger_mode = self.trigger.mode
                elif key in [ord("+"), ord("=")]:
                    self.trigger.increase_sensitivity()
                elif key in [ord("-"), ord("_")]:
                    self.trigger.decrease_sensitivity()

        finally:
            if self.cap is not None:
                self.cap.release()
            self.vcam.close()
            self.trigger.stop()
            cv2.destroyAllWindows()
            print("👋 ThanosCam closed.")


def main():
    parser = argparse.ArgumentParser(description="ThanosCam - Disintegrate into dust on video calls")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--width", type=int, default=640, help="Frame width (default: 640)")
    parser.add_argument("--height", type=int, default=480, help="Frame height (default: 480)")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS (default: 30)")
    args = parser.parse_args()

    config = AppConfig()
    config.camera_index = args.camera
    config.width = args.width
    config.height = args.height
    config.fps = args.fps

    app = CamDisappearApp(config=config)
    app.run()


if __name__ == "__main__":
    main()
