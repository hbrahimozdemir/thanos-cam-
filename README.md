<div align="center">

# 🌪️ CamDisappear (Thanos Endgame Exit)

**Disintegrate into dust and vanish from video calls with a snap of your fingers!**

*Real-time AI Segmentation, Vectorized 60 FPS Particle Physics, and Zero False-Trigger Multimodal Snap Detection for Google Meet, Zoom, Microsoft Teams & Discord.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![MediaPipe](https://img.shields.io/badge/AI-MediaPipe-orange.svg?logo=google&logoColor=white)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/hbrahimozdemir/thanos-cam/pulls)

<br/>

![Thanos Disappear Demo](thanos_disappear.gif)

</div>

---

## 🌟 Why CamDisappear?

Ever wanted to make an unforgettable, legendary exit from a boring or long meeting? 

**CamDisappear** turns you into ash like the Thanos snap in *Avengers: Endgame* right in the middle of a live video call. Your body crumbles into glowing embers and windblown dust, leaving only your completely empty chair behind!

Unlike simple novelty filters:
- 🌪️ **Cinematic Ash Effect:** Authentic, subtle clothing-and-skin sampled ash dust particles, natural fractal noise, and delicate charcoal dissolve boundaries.
- ⚡ **Zero False-Positives:** Natural hand-presence gating ensures your normal hand gestures while speaking won't accidentally trigger a disappearance.
- 🎙️ **"And I... Am... Iron Man" Voice Easter Egg:** Speak *"I am Iron Man"* into your microphone, and the snap will prime—snap your fingers to exit like Tony Stark in *Endgame*!
- 🚀 **Blazing Fast 60 FPS:** 100% vectorized NumPy particle physics simulating 25,000+ particles with < 2ms per-frame overhead.
- 📷 **Clean Virtual Camera Output:** Broadcasts directly to your video call software without watermarks or HUD overlays.

---

## 📸 Visual Breakdown

| 1. Live Video | 2. Armed & Snapped | 3. Disintegration & Embers | 4. Empty Chair |
| :---: | :---: | :---: | :---: |
| Full live webcam feed with MediaPipe human segmentation | Thumb & middle finger pinched to arm, followed by explosive release | Pockets of pixels ignite into embers and drift away with the wind | Voted out of reality. Only your empty chair remains! |

---

## 🛡️ The "Hand-Talker" Solution (Zero False Triggers)

If you gesticulate wildly while talking, traditional sound/motion triggers trigger constantly. CamDisappear solves this with **Multimodal Fusion & Intentional Arming**:

```
[Camera Feed]  ──> [MediaPipe Hand Landmarker] ──> [Thumb + Middle Finger Pinched >= 0.2s?]
                                                              │
                                                              ├─ NO  ──> [IGNORE: Regular hand gesturing]
                                                              └─ YES ──> [⚡ ARMED STATE: Ready to snap!]
                                                                             │
                                                                   [Explosive Finger Release]
                                                                             │
[Microphone]   ──> [2nd-Order High-Pass Filter] ──> [Audio Transient Spike <= 200ms?] ─┘
                   (Suppresses human voice by 170x)           │
                                                              ▼
                                                   [💥 SNAP TRIGGER FIRES!]
```

1. **Intentional Arming Dwell Time:** You must deliberately hold a Thumb-to-Middle-finger pinch for at least `0.2s`. Conversational hand movements never hold this static pose.
2. **2nd-Order Voice Suppression Filter:** Differential filtering eliminates human voice frequencies (100–1200 Hz) by over **170x**, responding strictly to impulsive high-frequency snap transients (3000–7000 Hz).
3. **Multimodal Synchronization Window:** The physical finger flick and acoustic click must coincide within a tight **200ms window**.

---

## 🚀 Quick Start

### Option A: Portable Standalone Executable (No Python Required)
1. Download the latest `ThanosCam.exe` from [GitHub Releases](https://github.com/hbrahimozdemir/thanos-cam/releases).
2. Double-click `ThanosCam.exe` and enjoy!

### Option B: Run from Source
#### 1. Requirements
- Python 3.10+
- A webcam and microphone
- [OBS Studio](https://obsproject.com/) *(for virtual camera streaming)*

#### 2. Installation
```bash
# Clone the repository
git clone https://github.com/hbrahimozdemir/thanos-cam.git
cd thanos-cam

# Install dependencies
pip install -r requirements.txt
```

### 3. Run
```bash
python main.py
```
*(On Windows, you can also double-click `run.bat`)*

Want to test the effect without plugging in a webcam?
```bash
python main.py --demo
```

---

## 🎮 Controls & Shortcuts

| Key | Action | Description |
| :---: | :--- | :--- |
| **`B`** | **Save Background** | Step out of frame and press `B` to cache the empty room plate (`background.jpg`). |
| **`S`** / **`Space`** | **Manual Snap** | Instantly triggers disintegration (safe fallback). |
| **`T`** | **Cycle Trigger Mode** | Switch between `HYBRID` ➔ `GESTURE` ➔ `AUDIO` ➔ `HOTKEY`. |
| **`+`** / **`=`** | **Sensitivity Up** | Lowers audio threshold for softer snaps. |
| **`-`** / **`_`** | **Sensitivity Down**| Raises audio threshold to ignore ambient background clatter. |
| **`R`** | **Reset & Reappear**| Restores live camera mode (I am inevitable!). |
| **`Q`** / **`ESC`** | **Quit** | Saves config and exits cleanly. |

---

## 🎥 Connecting to Google Meet, Zoom & Teams

1. Make sure **OBS Studio** is installed on your PC (this provides the system-level `OBS Virtual Camera` driver).
2. Launch `python main.py`.
3. Open your video meeting:
   - **Google Meet:** Settings (⋮) ➔ **Video** ➔ Camera: select **"OBS Virtual Camera"**.
   - **Zoom:** Settings (⚙️) ➔ **Video** ➔ Camera: select **"OBS Virtual Camera"**.
   - **Microsoft Teams:** Settings ➔ **Devices** ➔ Camera: select **"OBS Virtual Camera"**.
4. That's it! Your video feed is now streaming the live Thanos effect.

---

## ⚙️ Command-Line Options

```bash
usage: main.py [-h] [--camera CAMERA] [--width WIDTH] [--height HEIGHT]
               [--fps FPS] [--mode {hybrid,gesture,audio,hotkey}]
               [--wind {top_right,top_left,up}] [--demo] [--config CONFIG]

Options:
  --camera INT       Camera index (default: 0)
  --width INT        Capture resolution width (default: 640)
  --height INT       Capture resolution height (default: 480)
  --fps INT          Target frames per second (default: 30)
  --mode STR         Trigger mode: hybrid, gesture, audio, hotkey
  --wind STR         Wind direction: top_right, top_left, up
  --demo             Run in synthetic demo simulation mode
  --config PATH      Path to JSON configuration file (default: config.json)
```

---

## 🏗️ Architecture & Directory Layout

```
CamDisappear/
├── cam_disappear/
│   ├── engine/
│   │   ├── thanos_effect.py    # Vectorized particle engine with glowing embers
│   │   ├── trigger.py          # Multimodal gesture + audio snap fusion
│   │   ├── segmenter.py        # MediaPipe Selfie Segmenter wrapper
│   │   └── virtual_cam.py      # Virtual camera DirectShow bridge
│   └── config.py               # JSON configuration & defaults
├── main.py                     # CLI and interactive GUI runner
├── requirements.txt            # Python dependencies
├── README.md                   # Global documentation
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore rules
└── run.bat                     # Windows one-click launcher
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

<div align="center">
Made with ❤️ for everyone who ever wanted to leave a meeting in style.
</div>
