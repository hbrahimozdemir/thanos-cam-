"""
Virtual Camera stream manager using pyvirtualcam.
Supports OBS Virtual Camera and standalone UnityCapture drivers.
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
        self.device_name = "None"

        self._start_camera()

    def _start_camera(self):
        try:
            import pyvirtualcam

            # Try OBS first, fallback to unitycapture
            backends_to_try = [None, "obs", "unitycapture"]
            for backend in backends_to_try:
                try:
                    kwargs = {
                        "width": self.width,
                        "height": self.height,
                        "fps": self.fps,
                        "fmt": pyvirtualcam.PixelFormat.BGR,
                    }
                    if backend:
                        kwargs["backend"] = backend

                    self.vcam = pyvirtualcam.Camera(**kwargs)
                    self.is_active = True
                    self.device_name = str(self.vcam.device)
                    print(f"📷 [VirtualCam] Connected successfully to: {self.device_name}")
                    print(f"💡 Select '{self.device_name}' in Google Meet / Zoom / Teams.")
                    return
                except Exception:
                    continue

            print("[VirtualCam] Notice: No virtual camera driver found.")
            print("[VirtualCam] You can capture this window in OBS via 'Window Capture' and click 'Start Virtual Camera'.")
        except Exception as e:
            self.vcam = None
            self.is_active = False

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
