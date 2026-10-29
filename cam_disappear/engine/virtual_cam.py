"""
Virtual Camera stream manager using pyvirtualcam.
Automatically outputs composited video stream to Google Meet, Zoom, Teams, and Discord.
"""

import sys
import numpy as np


class VirtualCameraOutput:
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.vcam = None
        self.is_active = False

        self._start_camera()

    def _start_camera(self):
        try:
            import pyvirtualcam
            self.vcam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
            )
            self.is_active = True
            print(f"[VirtualCam] Connected successfully to: {self.vcam.device}")
            print(f"[VirtualCam] Select '{self.vcam.device}' in Google Meet / Zoom / Teams settings.")
        except Exception as e:
            self.vcam = None
            self.is_active = False
            print(f"[VirtualCam] Notice: No direct virtual camera driver found ({e}).")
            print("[VirtualCam] Tip: You can capture this window in OBS Studio via 'Window Capture' and click 'Start Virtual Camera'.")

    def send(self, frame: np.ndarray):
        if self.is_active and self.vcam is not None:
            self.vcam.send(frame)
            self.vcam.sleep_until_next_frame()

    def close(self):
        if self.vcam is not None:
            try:
                self.vcam.close()
            except Exception:
                pass
            self.is_active = False
