"""
Quick diagnostic script to test microphone sensitivity and snap detection.
Run: python test_audio.py
"""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import sounddevice as sd

print("=" * 60)
print("🎙️ MİKROFON VE ŞIKLATMA TEST ARACI")
print("Lütfen mikrofona doğru 2-3 kez parmak şıklatın...")
print("=" * 60)

max_peak = 0.0
max_crest = 0.0

def callback(indata, frames, time_info, status):
    global max_peak, max_crest
    samples = indata[:, 0].astype(np.float32)
    diff = np.diff(samples)
    peak = float(np.max(np.abs(diff)))
    rms = float(np.sqrt(np.mean(samples ** 2))) + 1e-5
    crest = peak / rms

    if peak > max_peak:
        max_peak = peak
    if crest > max_crest:
        max_crest = crest

    # Print meter if peak is noticeable
    if peak > 0.01:
        bar = "#" * int(min(50, peak * 200))
        print(f"Ses algılandı -> Peak: {peak:.4f} | Crest (Keskinlik): {crest:.1f} | [{bar}]")

try:
    with sd.InputStream(channels=1, samplerate=44100, blocksize=1024, callback=callback):
        time.sleep(5)
except Exception as e:
    print(f"Hata: {e}")

print("\n" + "=" * 60)
print(f"📊 Test Sonucu: En Yüksek Peak = {max_peak:.4f}, En Yüksek Crest = {max_crest:.1f}")
if max_peak < 0.02:
    print("⚠️ Mikrofon sesi çok kısık veya ses algılanamadı.")
    print("Windows Ses Ayarlarından mikrofon düzeyini artırmayı deneyin.")
else:
    print(f"✅ İdeal Eşik Değeri (Threshold): {max_peak * 0.5:.4f}")
print("=" * 60)
