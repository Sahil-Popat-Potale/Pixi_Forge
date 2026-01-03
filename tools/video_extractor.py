"""
tools/video_extractor.py

Utilities to extract frames from video files into image sequences.

Two backends:
  - ffmpeg (preferred): uses the system ffmpeg binary to extract frames as lossless PNGs.
  - opencv (fallback): uses cv2.VideoCapture and writes PNGs/JPEGs.

Functions return the number of frames written.
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple


def check_ffmpeg() -> bool:
    """
    Return True if ffmpeg is available in PATH.
    """
    return shutil.which("ffmpeg") is not None


def extract_frames_ffmpeg(
    video_path: str,
    output_dir: str,
    fmt: str = "png",
    prefix: str = "frame",
    start_time: Optional[float] = None,
    duration: Optional[float] = None,
    overwrite: bool = False,
) -> int:
    """
    Extract frames using ffmpeg.

    - fmt: "png" or "tiff" or "jpg" etc. PNG is recommended for lossless.
    - prefix: output file prefix, files will be prefix_000001.png, ...
    - start_time: seconds (float) to start extracting from (optional).
    - duration: seconds (float) total duration to extract (optional).
    - overwrite: if True, ffmpeg '-y' (overwrite existing), else '-n' (no overwrite).

    Returns number of files written.

    Raises:
      RuntimeError if ffmpeg isn't available or command fails.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    if not check_ffmpeg():
        raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg or use OpenCV backend.")

    # output pattern: frame_000001.png
    out_pattern = os.path.join(output_dir, f"{prefix}_%06d.{fmt}")

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start_time is not None:
        # seek before input for fast seek (accurate enough for most)
        cmd += ["-ss", str(start_time)]
    cmd += ["-i", video_path]
    if duration is not None:
        cmd += ["-t", str(duration)]

    # ensure one output per input frame (no frame duplication)
    cmd += ["-vsync", "0"]

    # choose overwrite behavior
    cmd += ["-y"] if overwrite else ["-n"]

    # For PNG output ffmpeg will automatically use lossless PNG encoding.
    cmd += [out_pattern]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e}") from e

    # Count how many files were created with the prefix and extension
    files = sorted(
        f for f in os.listdir(output_dir)
        if f.startswith(prefix + "_") and f.lower().endswith("." + fmt.lower())
    )
    return len(files)


def extract_frames_opencv(
    video_path: str,
    output_dir: str,
    fmt: str = "png",
    prefix: str = "frame",
) -> int:
    """
    Extract frames using OpenCV (cv2).
    Saves frames as PNG/JPEG with maximum quality (PNG compression=0, JPEG quality=100).

    Returns number of frames written.

    Requires: opencv-python installed.
    """
    try:
        import cv2
    except Exception as e:
        raise RuntimeError("OpenCV (cv2) not available. Install opencv-python.") from e

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    idx = 0
    written = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        idx += 1
        out_name = f"{prefix}_{idx:06d}.{fmt}"
        out_path = os.path.join(output_dir, out_name)

        # choose codec params for lossless-ish output
        if fmt.lower() in ("jpg", "jpeg"):
            # highest-quality jpeg
            ok = cv2.imwrite(out_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        elif fmt.lower() == "png":
            # PNG with no compression
            ok = cv2.imwrite(out_path, frame, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])
        else:
            ok = cv2.imwrite(out_path, frame)

        if not ok:
            # break on write failure
            cap.release()
            raise RuntimeError(f"Failed to write frame {out_path}")

        written += 1

    cap.release()
    return written


def extract_frames(
    video_path: str,
    output_dir: str,
    fmt: str = "png",
    prefix: str = "frame",
    backend: str = "ffmpeg",
    start_time: Optional[float] = None,
    duration: Optional[float] = None,
    overwrite: bool = False,
) -> Tuple[str, int]:
    """
    Convenience wrapper that selects the backend.

    Returns (backend_used, frames_written).
    """
    backend = backend.lower()
    if backend == "ffmpeg":
        if not check_ffmpeg():
            # try fallback
            backend = "opencv"

    if backend == "ffmpeg":
        count = extract_frames_ffmpeg(video_path, output_dir, fmt, prefix, start_time, duration, overwrite)
        return "ffmpeg", count
    elif backend == "opencv":
        count = extract_frames_opencv(video_path, output_dir, fmt, prefix)
        return "opencv", count
    else:
        raise ValueError("Unknown backend. Choose 'ffmpeg' or 'opencv'.")
