"""
CamDisappear - Thanos Disintegration Virtual Camera for Video Calls.
"""

import os
import sys
import time
import argparse

# Ensure robust cross-platform UTF-8 terminal output
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

        # Initialize AI Segmentation
        print("🧠 [1/4] MediaPipe Kişi Segmentasyonu yükleniyor...")
        self.segmenter = PersonSegmenter(self.config.model_segmenter_path)

        # Initialize Disintegration Particle Engine
        print("🌪️ [2/4] Thanos Kül Parçacık Motoru başlatılıyor...")
        self.effect = ThanosDisintegrationEngine(
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps,
        )

        # Initialize Multimodal Trigger Manager
        print("⚡ [3/4] Şıklatma ve El Algılayıcı başlatılıyor...")
        self.trigger = MultimodalTriggerManager(
            hand_model_path=self.config.model_hand_path,
            mode=self.config.trigger_mode,
            audio_threshold=0.018,
            cooldown=self.config.trigger_cooldown_sec,
        )

        # Initialize Virtual Camera Output
        print("📷 [4/4] Sanal Kamera Sürücüsüne bağlanılıyor...")
        self.vcam = VirtualCameraOutput(
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps,
        )

        # Load existing clean background if available
        self._load_saved_background()

    def _load_saved_background(self):
        if os.path.exists(self.config.background_path):
            img = cv2.imread(self.config.background_path)
            if img is not None:
                self.clean_background = cv2.resize(img, (self.config.width, self.config.height))
                print(f"✅ Kayıtlı boş sandalye yüklendi: {self.config.background_path}")

    def capture_background(self, frame: np.ndarray):
        """Saves current camera frame as the empty chair background plate."""
        self.clean_background = frame.copy()
        cv2.imwrite(self.config.background_path, self.clean_background)
        print(f"📸 Boş sandalye kaydedildi: {self.config.background_path}")

    def trigger_snap(self, frame: np.ndarray, mask: np.ndarray, source: str = "Manuel"):
        if self.clean_background is None:
            print("⚠️ UYARI: Önce sandalyeden kalkıp [B] tuşuna basarak boş sandalyenizi kaydedin!")
            return

        if self.state == "LIVE":
            print(f"💥 ŞIKLATMA ALGILANDI ({source})! Kül olarak dağılma başladı...")
            self.state = "DISINTEGRATING"
            self.effect.start(
                person_frame=frame,
                person_mask=mask,
                background_plate=self.clean_background,
                duration_sec=self.config.dissolve_duration_sec,
                wind_direction=self.config.wind_direction,
            )

    def reset_to_live(self):
        print("✨ Canlanılıyor (Kameraya dönüldü)...")
        self.effect.reset()
        self.state = "LIVE"

    def draw_hud(self, frame: np.ndarray):
        """Draws clean, non-overlapping HUD on local preview window."""
        h, w = frame.shape[:2]

        # Top and bottom bars
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 52), (18, 18, 22), -1)
        cv2.rectangle(overlay, (0, h - 35), (w, h), (18, 18, 22), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # 1. State indicator (Left)
        if self.state == "LIVE":
            st_text = "DURUM: CANLI"
            st_color = (0, 230, 100)
        elif self.state == "DISINTEGRATING":
            st_text = f"KUL OLUYOR... (%{int(self.effect.progress * 100)})"
            st_color = (100, 180, 255)
        else:
            st_text = "YOK OLDUNUZ (Sandalye Bos)"
            st_color = (0, 70, 255)

        cv2.putText(frame, st_text, (15, 26), cv2.FONT_HERSHEY_DUPLEX, 0.55, st_color, 1, cv2.LINE_AA)

        # Sub-status: Trigger Mode
        mode_text = f"Mod: {self.trigger.mode.upper()} [T]"
        cv2.putText(frame, mode_text, (15, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 220), 1, cv2.LINE_AA)

        # 2. Hand status (Center)
        if self.trigger.hand_visible:
            hand_str = "EL: HAZIR (Siklatabilirsiniz)"
            hand_col = (0, 255, 120)
        else:
            hand_str = "EL: Bekleniyor (Elinizi kaldirin)"
            hand_col = (140, 140, 140)

        cv2.putText(frame, hand_str, (int(w * 0.32), 32), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hand_col, 1, cv2.LINE_AA)

        # 3. Audio meter & threshold marker (Right)
        if self.trigger.audio_active:
            meter_w = 140
            meter_h = 14
            mx = w - meter_w - 15
            my = 12

            # Background meter bar
            cv2.rectangle(frame, (mx, my), (mx + meter_w, my + meter_h), (45, 45, 50), -1)

            # Audio peak level
            peak_val = self.trigger.recent_peak_decay
            fill_w = int(np.clip(peak_val * 1200, 0, meter_w))
            cv2.rectangle(frame, (mx, my), (mx + fill_w, my + meter_h), (0, 220, 255), -1)

            # Red threshold marker
            th = self.trigger.audio_threshold * (0.65 if self.trigger.hand_visible else 1.0)
            th_x = int(np.clip(mx + th * 1200, mx, mx + meter_w))
            cv2.line(frame, (th_x, my - 2), (th_x, my + meter_h + 2), (0, 0, 255), 2)

            cv2.putText(frame, f"Esik: {th:.3f} (+ / -)", (mx, my + meter_h + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)

        # 4. Bottom controls bar
        bg_status = "KAYITLI" if self.clean_background is not None else "YOK! (B'ye basin)"
        ctrl = f"[B] Sandalye: {bg_status} | [S/Space] Sikla | [R] Geri Don | [+/-] Hassasiyet | [Q] Cikis"
        cv2.putText(frame, ctrl, (12, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (210, 210, 210), 1, cv2.LINE_AA)

    def run(self):
        print(f"🎥 Web Kamerası {self.config.camera_index} açılıyor...")
        cap = cv2.VideoCapture(self.config.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.config.camera_index)

        if not cap.isOpened():
            print(f"❌ HATA: Web kamerası (Index: {self.config.camera_index}) açılamadı!")
            print("Lütfen kameranızın başka bir program (Teams, Zoom, Tarayıcı) tarafından kullanılmadığından emin olun.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)

        cv2.namedWindow("CamDisappear (Thanos Cam)", cv2.WINDOW_AUTOSIZE)

        print("\n" + "=" * 60)
        print("🚀 CAMDISAPPEAR ÇALIŞIYOR!")
        print("  1. [B] tuşuna basın -> Boş sandalyenizi kaydedin.")
        print("  2. Elinizi kaldırıp parmağınızı şıklatın -> Kül olarak yok olun!")
        print("  3. [R] tuşuna basın -> Geri dönün.")
        print("  4. [S] veya [Space] -> Acil manuel çıkış.")
        print("  5. [+] ve [-] -> Mikrofon şıklatma hassasiyetini ayarlayın.")
        print("=" * 60 + "\n")

        try:
            while True:
                ret, raw_frame = cap.read()
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
                        print("💀 Vücut kül oldu. Sandalye boş.")
                elif self.state == "DISAPPEARED":
                    clean_output_frame = self.clean_background.copy()

                # Stream to Virtual Camera
                self.vcam.send(clean_output_frame)

                # Local Preview Window with HUD
                hud_frame = clean_output_frame.copy()
                self.draw_hud(hud_frame)
                cv2.imshow("CamDisappear (Thanos Cam)", hud_frame)

                # Key controls
                key = cv2.waitKey(1) & 0xFF
                if key in [ord("q"), ord("Q"), 27]:
                    break
                elif key in [ord("b"), ord("B")]:
                    self.capture_background(raw_frame)
                elif key in [ord("s"), ord("S"), 32]:  # S or Space
                    mask = self.segmenter.get_mask(raw_frame)
                    self.trigger_snap(raw_frame, mask, source="Klavye Kısayolu")
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
            if cap is not None:
                cap.release()
            self.vcam.close()
            self.trigger.stop()
            cv2.destroyAllWindows()
            print("👋 CamDisappear kapatıldı.")


def main():
    parser = argparse.ArgumentParser(description="CamDisappear - Thanos Disintegration Virtual Camera")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index")
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
