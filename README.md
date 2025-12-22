# PixelForge — Intelligent Image Slicing Tool

PixelForge is a professional-grade image slicing system that combines
pixel-perfect deterministic slicing with optional OpenCV-based intelligent slicing.
It supports batch processing, command-line automation, and a real-time,
explainable GUI that visually shows how and why images are split.

The project is designed to be safe, modular, and transparent rather than “magic”.

---

## ✨ Key Features

- Pixel-perfect horizontal, vertical, and grid slicing
- Intelligent (OpenCV-based) smart slicing with safe fallback
- Batch folder processing with logging
- Command-line interface (CLI) for automation
- Responsive Tkinter GUI with live preview
- Explainable smart slicing via heatmap visualization
- No silent failures, no destructive operations

---

## 📁 Project Structure

```

pixel_forge/
│
├── core/        # Core slicing engine (deterministic, pixel-perfect)
├── smart/       # OpenCV-based intelligent slicing
├── batch/       # Batch automation + logging
├── cli/         # Command-line interface
├── gui/         # Tkinter GUI application
│
├── pixelforge.py        # CLI entry point
├── input_images/        # Images to process (user provided)
├── output_images/       # Generated output images
├── logs/                # Runtime logs
│
├── test_core.py         # Manual core tests
├── test_smart.py        # Manual smart slicing tests
├── test_batch.py        # Manual batch tests
└── README.md

````

---

## 🛠️ Installation

### 1. Requirements

- Python **3.10 or higher**
- OS: Windows / Linux / macOS (GUI tested primarily on Windows)

### 2. Install dependencies

```bash
pip install pillow opencv-python numpy
````

Tkinter comes pre-installed with standard Python distributions.

---

## 🚀 How to Use

PixelForge can be used in **three ways**:

---

### 1️⃣ GUI Application (Recommended)

Launch the GUI:

```bash
python -c "from gui.app import launch; launch()"
```

**GUI capabilities:**

* Select input and output folders
* Choose slicing mode (horizontal / vertical / grid)
* Enable smart slicing (horizontal only)
* See real-time preview with slice lines
* View smart slicing heatmap (blue → green → yellow → red)
* Run batch processing safely

**Legend (Smart Preview):**

* 🔵 Blue: very safe cut zone
* 🟢 Green: safe
* 🟡 Yellow: risky
* 🔴 Red: unsafe (dense content)
* ⚪ White lines: deterministic slicing
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
from batch import BatchImageProcessor

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

## 🧠 How Smart Slicing Works (Important)

Smart slicing:

* Uses OpenCV edge detection
* Analyzes vertical edge energy
* Finds low-content (quiet) columns
* Refuses to slice if no safe cuts exist

If smart slicing fails:
➡️ The system **automatically falls back** to deterministic slicing.

This behavior is intentional and ensures:

* No random guesses
* No broken images
* No crashes

---

## ⚠️ Known Limitations (By Design)

* Smart slicing works best on:

  * banners
  * slides
  * images with clear vertical gaps
* Smart slicing will usually fail on:

  * portraits
  * anime art
  * collages
  * dense photographs

This is expected and visible via the GUI heatmap.

---

## 🧪 Testing

Manual test scripts are provided:

```bash
python test_core.py
python test_smart.py
python test_batch.py
```

These validate:

* slicing math
* smart slicing behavior
* batch fallback safety

---

## 🔒 Safety & Reliability Notes

* Input images are never modified
* All outputs go to a separate directory
* Errors are logged, not hidden
* No external network calls
* No shell execution
* No dynamic code execution

---

## 📌 Future Enhancements (Optional)

* Save/load GUI presets
* Package as Windows `.exe`
* Advanced smart slicing (grid-aware)
* Unit tests (pytest)
* Documentation screenshots

---

## 🙌 Final Note

PixelForge is built with correctness, transparency, and user trust as first principles.
It favors safe failure over silent guessing — and explains its decisions visually.

That is a feature, not a limitation.

```