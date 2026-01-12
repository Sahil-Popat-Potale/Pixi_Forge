# Pixi Forge — Intelligent Image Slicing Tool

Pixi Forge is a professional-grade image slicing system that combines
pixel-perfect deterministic slicing with optional OpenCV-based intelligent slicing.
It supports batch processing, command-line automation, and a real-time,
explainable GUI that visually shows how and why images are split.

Pixi Forge is designed to be safe, modular, and transparent rather than “magic”.

---

## ✨ Key Features

- Pixel-perfect horizontal, vertical, and grid slicing
- Intelligent (OpenCV-based) smart slicing with safe fallback
- Batch folder processing with logging
- Command-line interface (CLI) for automation
- Responsive Tkinter GUI with live preview
- Explainable smart slicing via heatmap visualization
- Video → Frames extraction (lossless PNG via `ffmpeg`, OpenCV fallback)
- No silent failures, no destructive operations

---

## 📁 Project Structure

```

Pixi_Forge/
│
├── core/        # Core slicing engine (deterministic, pixel-perfect)
├── smart/       # OpenCV-based intelligent slicing
├── batch/       # Batch automation + logging
├── cli/         # Command-line interface
├── gui/         # Tkinter GUI application
├── tools/       # Utility tools (video frame extractor, etc.)
│
├── run_gui.py        # GUI entry point (recommended)
├── pixelforge.py     # CLI entry point
├── input_images/     # Images to process (user provided)
├── output_images/    # Generated output images
├── logs/             # Runtime logs
│
├── test_core.py      # Manual core tests
├── test_smart.py     # Manual smart slicing tests
├── test_batch.py     # Manual batch tests
└── README.md

````

---

## 🛠️ Installation

### Requirements

- Python **3.10 or higher**
- OS: Windows / Linux / macOS (GUI tested primarily on Windows)
- Optional (recommended): `ffmpeg` binary in your PATH for best video frame extraction

### Install Python dependencies

From project root:

```bash
pip install -r requirements.txt
````

If you don't have `requirements.txt`, install the core packages:

```bash
pip install pillow opencv-python numpy
```

Notes:

* Use `opencv-python` (not `-headless`) if you plan to use the GUI or `cv2.imshow` features.
* `Tkinter` is bundled with most Python distributions (standard on Windows/macOS).

### Install ffmpeg (optional but recommended)

ffmpeg is recommended for video → frames extraction (lossless PNG output and robust codec handling).

* On Windows: download `ffmpeg.exe` and add it to your PATH.
* On macOS: `brew install ffmpeg`
* On Linux: use your distro package manager, e.g. `sudo apt install ffmpeg`.

If `ffmpeg` is not present, Pixi Forge falls back to OpenCV for frame extraction (still works but codec handling is less robust).

---

## 🚀 How to Use

Pixi Forge can be used in **three ways**.

---

### 1️⃣ GUI Application (Recommended)

Launch the GUI:

```bash
python run_gui.py
```

Or (alternate):

```bash
python -c "from gui.app import launch; launch()"
```

**GUI capabilities**

* Select input and output folders
* Choose slicing mode (horizontal / vertical / grid)
* Enable smart slicing (horizontal only)
* See real-time preview with deterministic slice lines (white)
* View smart slicing heatmap (blue → green → yellow → red)
* Run batch processing safely
* Extract frames from video via the Tools → Video Extractor button (if enabled)

**Legend (Smart Preview):**

* 🔵 Blue: very safe cut zone
* 🟢 Green: safe
* 🟡 Yellow: risky
* 🔴 Red: unsafe (dense content)
* ⚪ White lines: deterministic slicing boundaries
* 🟢 Thick green lines: smart candidate splits

---

### 2️⃣ Command Line Interface (CLI)

Basic usage:

```bash
python pixelforge.py input_images output_images --mode horizontal --n 5
```

Grid slicing:

```bash
python pixelforge.py input_images output_images --mode grid --rows 3 --cols 4
```

Smart slicing with fallback:

```bash
python pixelforge.py input_images output_images --mode horizontal --n 5 --smart --logs logs
```

**Exit codes:**

* `0` → success
* `1` → completed with some failures
* `2` → invalid arguments or runtime error

---

### 3️⃣ Batch Processing (Python API)

```python
from batch.processor import BatchImageProcessor

processor = BatchImageProcessor(
    input_dir="input_images",
    output_dir="output_images",
    log_dir="logs"
)

result = processor.process(
    mode="horizontal",
    n=3,
    smart=True
)

print(result.processed)
print(result.failed)
```

---

## 🎞️ Video → Frames (new feature)

Pixi Forge can extract every frame from a video to an image sequence (lossless PNG recommended).

Tools:

* `tools/video_extractor.py` — exposes `extract_frames(...)`
* CLI helper: `python -m tools.extract_frames_cli <video> <outdir> [--fmt png] [--backend auto]`

Example (automatic backend detection):

```bash
python -m tools.extract_frames_cli sample.mp4 frames_out --fmt png --backend auto
```

Example (explicit backend):

```bash
python -m tools.extract_frames_cli sample.mp4 frames_out --fmt png --backend ffmpeg
```

Python API:

```python
from tools.video_extractor import extract_frames

backend_used, frames_written = extract_frames("sample.mp4", "frames_out", fmt="png", backend="ffmpeg")
print(backend_used, frames_written)
```

Notes:

* `ffmpeg` backend is recommended for fidelity and codec support. It writes `frame_000001.png`, etc.
* `opencv` backend is used as a fallback if `ffmpeg` is unavailable.
* Warning: extracting all frames from long/high-FPS videos consumes disk space. Consider extracting ranges or sample rates.

---

## 🧠 How Smart Slicing Works (Important)

Smart slicing:

* Uses OpenCV edge detection (Canny)
* Computes column-wise edge energy
* Finds low-content (quiet) vertical columns suitable for safe splits
* Picks candidate split positions and refuses to split if candidates are ambiguous

If smart slicing fails:
➡️ The system **automatically falls back** to deterministic slicing.

This ensures:

* No guessing
* No corrupted outputs
* Predictable behavior

---

## ⚠️ Known Limitations (By Design)

Smart slicing works best on:

* banners, slides, promotional images
* images with clear vertical gaps

Smart slicing will usually fail on:

* portraits and close-ups
* anime art and dense illustrations
* collages and busy photographs

When smart slicing fails, the GUI heatmap will show high energy (red/yellow) and smart mode will fall back to deterministic slicing.

---

## 📸 Screenshots

Add these images to `/screenshots` (project root) and they will render on GitHub.

```
screenshots/
├── 01_main_gui.png
├── 02_deterministic_preview.png
├── 03_smart_heatmap.png
├── 04_smart_refusal.png
├── 05_batch_complete.png
├── 06_video_extract_cli.png
├── 07_video_extract_gui.png
```

Suggested README snippet to include (drop into README where appropriate):

```markdown
## 📸 Screenshots

### 1️⃣ Main GUI — Initial State
![Main GUI](screenshots/01_main_gui.png)

### 2️⃣ Live Preview — Deterministic Slicing
![Deterministic Preview](screenshots/02_deterministic_preview.png)

### 3️⃣ Smart Preview — Heatmap Overlay
![Smart Heatmap Preview](screenshots/03_smart_heatmap.png)

### 4️⃣ Smart Slicing Refusal (Explainable Failure)
![Smart Refusal](screenshots/04_smart_refusal.png)

### 5️⃣ Batch Processing Completion
![Batch Complete](screenshots/05_batch_complete.png)

### 6️⃣ Video Extract — CLI Example
![Video CLI](screenshots/06_video_extract_cli.png)

### 7️⃣ Video Extract — GUI Example
![Video GUI](screenshots/07_video_extract_gui.png)
```

How to take clean screenshots:

* Keep window at the default size (no odd scaling)
* Use one clean sample image or video for each case:

  * Banner/slide for smart success
  * Portrait for smart refusal
  * Folder with multiple images for batch
  * Short sample video for frame extraction
* Crop tightly to the application window; avoid desktop clutter

---

## 🧪 Testing

Manual test scripts:

```bash
python test_core.py
python test_smart.py
python test_batch.py
```

Video frame extraction test:

```bash
python -m tools.extract_frames_cli sample.mp4 frames_out --fmt png --backend auto
```

Sanity-check GUI:

1. Launch GUI: `python run_gui.py`
2. Select an `input_images` folder
3. Switch modes, play with `n`, `rows`, `cols`
4. Enable Smart (horizontal) and observe heatmap + candidate lines
5. Run Batch Processing; check `/output_images` and `/logs`

---

## 🔒 Safety & Reliability Notes

* Input images/videos are never modified in place
* All outputs go to separate directories
* Errors are logged and surfaced to the user
* No external network calls by default
* No shell execution besides optional `ffmpeg` subprocess (explicit and controlled)
* No dynamic code execution

---

## 📝 Contributing

* Open issues for bugs or feature requests
* Send PRs to `main` with tests or screenshots
* Follow code style (type hints preferred, docstrings for public APIs)

---

## ⚙ Troubleshooting (common problems)

**`ModuleNotFoundError: No module named 'tools'`**

* Run from project root or run as module:

  ```bash
  python -m tools.extract_frames_cli ...
  ```
* Ensure `tools/__init__.py` exists.

**`ffmpeg not found`**

* Install ffmpeg or pass `--backend opencv` (requires `opencv-python`).

**Pylance / linter warnings in VS Code**

* Many GUI/Tkinter warnings are type-stub artifacts. The code runs correctly; apply per-line `# type: ignore` only where necessary.

---

## Final thoughts

Pixi Forge favors **clarity, correctness, and explainability**. When intelligence chooses not to act (smart slicing refuses), that decision is shown visually. That transparency is intentional — it builds trust.
