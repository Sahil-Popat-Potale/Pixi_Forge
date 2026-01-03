#!/usr/bin/env python3
"""
Robust CLI wrapper for tools/video_extractor.py

Works whether run from project root or from tools/ directly.
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path so `tools` package can be imported.
# If this file is run directly, __file__ is tools/extract_frames_cli.py; parent parent is project root.
this_file = Path(__file__).resolve()
project_root = this_file.parents[1]  # parent of `tools/`
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now safe to import
from tools.video_extractor import extract_frames, check_ffmpeg  # type: ignore

def main():
    p = argparse.ArgumentParser(description="Extract frames from video (Pixi Forge helper).")
    p.add_argument("video", type=Path, help="Input video file")
    p.add_argument("outdir", type=Path, help="Output directory for frames")
    p.add_argument("--fmt", default="png", help="Image format (png, jpg, tiff). Default: png")
    p.add_argument("--prefix", default="frame", help="Output filename prefix")
    p.add_argument("--backend", choices=["ffmpeg", "opencv", "auto"], default="auto")
    p.add_argument("--start", type=float, default=None, help="Start time in seconds")
    p.add_argument("--duration", type=float, default=None, help="Duration in seconds")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing frames")
    args = p.parse_args()

    backend = args.backend
    if backend == "auto":
        backend = "ffmpeg" if check_ffmpeg() else "opencv"

    print(f"Using backend: {backend}")
    backend_used, count = extract_frames(
        str(args.video),
        str(args.outdir),
        fmt=args.fmt,
        prefix=args.prefix,
        backend=backend,
        start_time=args.start,
        duration=args.duration,
        overwrite=args.overwrite,
    )
    print(f"Frames written: {count} (backend: {backend_used})")

if __name__ == "__main__":
    main()
