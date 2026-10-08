# 🎬 Video to GIF Converter Software

A modern desktop application built with Python & CustomTkinter that converts video files into high-quality GIFs. Features real-time video playback preview, interactive video clipping/trimming controls, speed adjustment (playback multiplier), resolution scaling, and high-quality 2-pass palette optimization.

---

## ✨ Features

- **✂ Interactive Video Trimming / Clipping**:
  - Set exact `Start Time` and `End Time` in seconds using sliders or text inputs.
  - "Set Start at Current" & "Set End at Current" buttons to trim based on live video playback frame.
  - Live preview scrubber with frame step (`⏮` / `⏭`) and video frame timestamp display.

- **⚡ Video Speed Adjustment (GIF Alignment)**:
  - Modify playback speed from `0.25x` (slow motion) up to `4.0x` (fast forward).
  - Quick preset buttons (`0.5x`, `0.75x`, `1.0x`, `1.25x`, `1.5x`, `2.0x`).
  - Displays effective output GIF loop duration in real-time (e.g. `3.0s trim @ 1.5x speed = 2.0s GIF`).

- **⚙ GIF Quality & Optimization Controls**:
  - **Resolution Scaling**: 320p, 480p, 640p, 720p, or Original resolution (maintains aspect ratio).
  - **Frame Rate (FPS)**: Choose between 10, 15, 20, 24, or 30 FPS.
  - **Color Palette Optimization**: 2-pass FFmpeg PaletteGen filter (`sierra2_4a` dithering) for vibrant, crisp color rendition without heavy noise artifacts.

- **🚀 Performance & Modern UI**:
  - Dark Mode GUI powered by `CustomTkinter`.
  - Multithreaded background processing ensures smooth UI without lagging or freezing.
  - Automatic directory opening upon completion.

---

## 🚀 How to Run

### Option 1: Double-Click Launcher (Windows)
Double-click `run_app.bat`.

### Option 2: Command Line
```bash
python app.py
```

---

## 🛠 Dependencies

Installed automatically via pip:
- `customtkinter` (Modern Dark Mode UI framework)
- `opencv-python` (Video decoding and frame rendering)
- `pillow` (Image processing)
- `imageio` & `imageio-ffmpeg` (FFmpeg binary & GIF encoding engine)

To install dependencies manually:
```bash
pip install -r requirements.txt
```

---

## 🧪 Running Automated Tests

Run the test suite to verify video processing, clipping, speed adjustment, and GIF creation:
```bash
python test_converter.py
```

---

## 📁 Project Structure

```
├── app.py                # Main CustomTkinter GUI application
├── converter.py          # FFmpeg video processing & GIF engine
├── test_converter.py     # Automated unit & integration tests
├── requirements.txt      # Dependencies
├── run_app.bat           # Windows launcher script
└── README.md             # Documentation
```
