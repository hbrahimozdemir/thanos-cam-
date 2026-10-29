"""
High-Sensitivity Audio Snap Detector using sounddevice.
Detects finger snaps via high-frequency transient spike and crest factor.
Includes real-time sensitivity adjustment and visual meters.
"""

import time
import numpy as np
import sounddevice as sd


class AudioSnapDetector:
    def __init__(self, sample_rate: int = 44100, block_size: int = 1024, threshold: float = 0.04):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.threshold = threshold          # Default lowered for high sensitivity
        self.is_running = False
        self.stream = None

        # State
        self.snapped = False
        self.last_snap_time = 0.0
        self.cooldown_sec = 2.5

        # Visual telemetry for HUD
        self.current_peak = 0.0
        self.current_rms = 0.0
        self.current_crest = 0.0
        self.recent_peak_decay = 0.0
        self.rolling_floor = 0.005

        # External boost flag (e.g. boosted when hand is visible in frame)
        self.boost_active = False

    def increase_sensitivity(self):
        """Lowers threshold by 20% (makes it easier to snap)."""
        self.threshold = max(0.008, self.threshold * 0.8)
        print(f"🔊 Hassasiyet Artırıldı (Eşik: {self.threshold:.4f})")

    def decrease_sensitivity(self):
        """Raises threshold by 25% (requires louder snap)."""
        self.threshold = min(0.30, self.threshold * 1.25)
        print(f"🔉 Hassasiyet Azaltıldı (Eşik: {self.threshold:.4f})")

    def _audio_callback(self, indata, frames, time_info, status):
        samples = indata[:, 0].astype(np.float32)

        # High-pass filter via first-order difference (isolates sharp high-frequency transient clicks)
        diff = np.diff(samples)
        peak = float(np.max(np.abs(diff)))
        rms = float(np.sqrt(np.mean(samples ** 2))) + 1e-5
        crest = peak / rms

        self.current_peak = peak
        self.current_rms = rms
        self.current_crest = crest

        # Smooth peak decay for HUD visual bar
        if peak > self.recent_peak_decay:
            self.recent_peak_decay = peak
        else:
            self.recent_peak_decay *= 0.90

        # Slow noise floor tracker
        self.rolling_floor = 0.98 * self.rolling_floor + 0.02 * rms

        # Active threshold (lowered by 40% if hand is visible!)
        effective_threshold = self.threshold * (0.6 if self.boost_active else 1.0)

        now = time.time()

        # SNAP CRITERIA:
        # 1. Peak transient exceeds effective threshold
        # 2. Crest factor > 2.8 (sharp attack relative to overall loudness, distinguishing snaps from speech)
        # 3. Peak is at least 2.5x above ambient noise floor
        # 4. Cooldown has passed
        if (
            peak > effective_threshold
            and crest > 2.8
            and (peak / (self.rolling_floor + 1e-4)) > 2.2
            and (now - self.last_snap_time) > self.cooldown_sec
        ):
            self.snapped = True
            self.last_snap_time = now

    def start(self):
        """Starts background audio stream."""
        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.is_running = True
            return True
        except Exception as e:
            print(f"[AudioSnapDetector] Uyarı: Mikrofon başlatılamadı ({e}).")
            self.is_running = False
            return False

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.is_running = False

    def check_snap(self) -> bool:
        """Returns True if snap occurred, then resets flag."""
        if self.snapped:
            self.snapped = False
            return True
        return False
